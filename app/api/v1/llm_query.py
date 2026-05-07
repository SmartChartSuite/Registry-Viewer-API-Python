import os
import logging
from fastapi import APIRouter, Path, Query, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from typing import List, Optional
import httpx
import base64

from app.db.base import get_async_session
from app.schemas.model_case import ModelCase
from app.schemas.case_data import LlmResultData
from app.security.deps import get_current_user
from app.schemas.metadata import Error

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["llm-query-controller"],
)

# ---------------------------------------------------------------------------
# Environment Variables & Configuration
# ---------------------------------------------------------------------------
# Testing environment variables
TESTER_URL = os.getenv("TESTER_URL") # Format: jdbc:postgresql://... (need to convert to asyncpg)
TESTER_DATABASE = os.getenv("TESTER_DATABASE")
TESTER_USERNAME = os.getenv("TESTER_USERNAME")
TESTER_PASSWORD = os.getenv("TESTER_PASSWORD")
TESTER_CDM_SCHEMA = os.getenv("TESTER_CDM_SCHEMA")
TESTER_VOCAB_SCHEMA = os.getenv("TESTER_VOCAB_SCHEMA")
SERVER_TESTING = os.getenv("SERVER_TESTING", "no").lower()

# LLM Server Configuration
LLM_API_SERVER_GENERATE_QUERY_URL = os.getenv("LLM_API_SERVER_GENERATE_QUERY_URL")
LLM_API_SERVER_INTERPRETATION_URL = os.getenv("LLM_API_SERVER_INTERPRETATION_URL")
LLM_API_SERVER_AUTH_BASIC = os.getenv("LLM_API_SERVER_AUTH_BASIC") # format "user:pass"

# Standard Production Env
VOCABULARY_SCHEMA = os.getenv("VOCABULARY_SCHEMA")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_NAME = os.getenv("DATABASE_NAME")

def get_basic_auth_header():
    if not LLM_API_SERVER_AUTH_BASIC:
        return None
    auth_str = LLM_API_SERVER_AUTH_BASIC
    encoded_auth = base64.b64encode(auth_str.encode()).decode()
    return {"Authorization": f"Basic {encoded_auth}"}

def convert_jdbc_to_asyncpg(jdbc_url: str) -> str:
    """Converts jdbc:postgresql://host:port/db to postgresql+asyncpg://host:port/db
    Also handles host only format by adding postgresql+asyncpg:// prefix
    """
    if not jdbc_url:
        return ""
    # If it's already in jdbc format, convert it
    if jdbc_url.startswith("jdbc:postgresql://"):
        return jdbc_url.replace("jdbc:postgresql://", "postgresql+asyncpg://")
    # If it's just a hostname, assume postgresql protocol
    elif not jdbc_url.startswith("postgresql://") and not jdbc_url.startswith("postgresql+asyncpg://"):
        return f"postgresql+asyncpg://{jdbc_url}"
    # If it's already in postgresql format, return as-is
    return jdbc_url

# ---------------------------------------------------------------------------
# Helper to fetch ModelCase from person_id
# ---------------------------------------------------------------------------
async def get_model_case_by_person_id(db: AsyncSession, person_id: int, registry: str):
    """
    Reuses the ModelCase construction logic. 
    Since we can't easily import the loop from search_cases.py without refactoring,
    we implement a focused query here.
    """
    sql = f"""
        SELECT
            ci.case_info_id AS case_id,
            ci.activated_datetime,
            ci.created_datetime,
            ci.trigger_at_datetime,
            ci.last_updated_datetime,
            ci.last_successful_datetime,
            ci.case_started_running_datetime,
            fp.family_name,
            fp.given1_name,
            fp.given2_name,
            c.concept_name AS gender_concept_name,
            p.year_of_birth,
            p.month_of_birth,
            p.day_of_birth,
            fp.contact_point1,
            fp.contact_point2,
            fp.contact_point3,
            loc.address_1,
            loc.address_2,
            loc.city,
            loc.state,
            loc.zip,
            ci.status
        FROM {registry}.person AS p
        JOIN {registry}.f_person AS fp ON p.person_id = fp.person_id
        JOIN {registry}.case_info AS ci ON p.person_id = ci.person_id
        LEFT JOIN {registry}.location AS loc ON ci.location_id = loc.location_id
        LEFT JOIN {VOCABULARY_SCHEMA if not (SERVER_TESTING == "yes") else TESTER_VOCAB_SCHEMA}.concept AS c ON p.gender_concept_id = c.concept_id
        WHERE p.person_id = :person_id
    """
    result = await db.execute(text(sql), {"person_id": person_id})
    row = result.fetchone()
    if not row:
        return None

    # Logic mirrored from search_cases.py
    dob = None
    if row[11] is not None and row[12] is not None and row[13] is not None:
        try:
            dob = f"{int(row[11]):04d}-{int(row[12] or 1):02d}-{int(row[13] or 1):02d}"
        except: dob = None
    
    street = " ".join(filter(None, [str(row[17]), str(row[18])])) if any([row[17], row[18]]) else None
    
    phone = None
    for cp in [row[14], row[15], row[16]]:
        if cp:
            parts = cp.split(':')
            if len(parts) >= 3 and parts[0].lower() in {"phone", "mobile"}:
                phone = parts[2].strip()
                break
    
    # Status mapping
    status_obj = None
    if row[22]:
        from app.schemas.metadata import Status
        status_mapping = {
            "RUNNING": {"ui_code": "information", "ui_description": "Case is running in normal mode."},
            "END": {"ui_code": "information", "ui_description": "Case is outside of monitoring period and not tracked."},
            "REQUEST_PENDING": {"ui_code": "information", "ui_description": "Job is pending. The number of allowed concurrent jobs can be configured."},
            "TIMED_OUT": {"ui_code": "timed-out", "ui_description": "Job taking longer than expected. This may indicate a temporary network error. If this error persists, please contact technical support. (0x0008)."},
            "PAUSED": {"ui_code": "paused", "ui_description": "Case is paused by system administrator. (0x0010)"},
            "ERROR_IN_CLIENT": {"ui_code": "fatal", "ui_description": "Registry internal error occurred. Please contact technical support (0x0100)."},
            "ERROR_IN_SERVER": {"ui_code": "fatal", "ui_description": "Registry encountered an error in the backend services. Please contact technical support (0x0200)."},
            "RESULT_PARSE_ERROR": {"ui_code": "fatal", "ui_description": "Registry encountered an error with Data Received from provider. Please contact technical support (0x0201)."},
            "ERROR_UNKNOWN": {"ui_code": "error", "ui_description": "Error occurred during data import to registry. Please contact technical support (0x0400)"},
            "INVALID": {"ui_code": "warning", "ui_description": "not in use (0x0000)"}
        }
        s_info = status_mapping.get(str(row[22]).strip(), {"ui_code": "unknown", "ui_description": f"Unknown status: {row[22]}"})
        status_obj = Status(
            activatedDateTime=row[1].isoformat() if row[1] else None,
            caseStartedRunningDateTime=row[6].isoformat() if row[6] else None,
            code=s_info["ui_code"],
            createdDateTime=row[2].isoformat() if row[2] else None,
            detail=s_info["ui_description"],
            lastSuccessfulDateTime=row[5].isoformat() if row[5] else None,
            nextScheduledDateTime=row[3].isoformat() if row[3] else None
        )

    return ModelCase(
        caseId=row[0],
        city=row[19],
        dob=dob,
        firstName=row[8],
        gender=row[10],
        initialReportDate=row[1].isoformat() if row[1] else None,
        lastName=row[7],
        phone=phone,
        state=row[20],
        status=status_obj,
        street=street,
        zip=row[21]
    )

# ---------------------------------------------------------------------------
# GET endpoint – llm query
# ---------------------------------------------------------------------------
@router.get(
    "/registry-viewer-api/llm-query/{registry}",
    response_model=LlmResultData,
    responses={
        200: {"description": "AI-generated query results"},
        400: {"model": Error, "description": "Bad request – invalid parameters"},
        422: {"description": "Unprocessable Entity - LLM server response not JSON"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
)
async def llm_query(
    registry: str = Path(..., description="Registry Path"),
    query: str = Query(..., description="question to be posed"),
    type: str = Query("population", description="population or patient"),
    caseId: Optional[int] = Query(None, description="caseId for patient query"),
    db: AsyncSession = Depends(get_async_session),
    auth: dict = Depends(get_current_user),
):
    # 1. Validation: If type == 'patient', caseId must be provided
    if type == "patient" and caseId is None:
        raise HTTPException(
            status_code=400, 
            detail={"code": 400, "message": "caseId must be provided when type is 'patient'"}
        )

    # 2. Determine schemas and database config based on SERVER_TESTING
    if SERVER_TESTING == "yes":
        cdm_schema = TESTER_CDM_SCHEMA
        vocab_schema = TESTER_VOCAB_SCHEMA
        # Use a separate engine for tester DB if different from main db
        use_tester_db = True
    else:
        cdm_schema = registry
        vocab_schema = VOCABULARY_SCHEMA
        use_tester_db = False

    # 3. Construct "ResultsList" payload
    results_list = {
        "user_command": query,
        "query_type": type,
        "cdm_schema": cdm_schema,
        "vocab_schema": vocab_schema
    }

    # 4. Call LLM_API_SERVER_GENERATE_QUERY_URL
    headers = get_basic_auth_header()
    async with httpx.AsyncClient() as client:
        try:
            gen_resp = await client.post(
                LLM_API_SERVER_GENERATE_QUERY_URL, 
                json=results_list, 
                headers=headers, 
                timeout=60.0
            )
            gen_resp.raise_for_status()
            gen_data = gen_resp.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="LLM Generation Server Error")
        except (httpx.RequestError, ValueError):
            # Return 422 UNPROCESSABLE_ENTITY if not JSON or request failed
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                detail={"code": 422, "message": "LLM server response is not a valid JSON object"}
            )

    # 5. Process LLM generation results
    sql_query = gen_data.get("query")
    returned_schema = gen_data.get("cdm_schema")

    if returned_schema != TESTER_CDM_SCHEMA:
        logger.error(f"LLM returned schema {returned_schema} which differs from TESTER_CDM_SCHEMA {TESTER_CDM_SCHEMA}")

    # 6. Execute the generated SQL
    sql_results = []
    if use_tester_db:
        # Create temporary engine for tester database
        async_url = convert_jdbc_to_asyncpg(TESTER_URL)
        engine = create_async_engine(
            async_url, 
            # In a real scenario, you'd use the provided TESTER_USERNAME/PASSWORD in the URL
            # but here we assume the URL is configured or we'd build it from parts.
        )
        # Note: Normally we'd use a sessionmaker. For simplicity in this API call:
        async with engine.begin() as conn:
            res = await conn.execute(text(sql_query))
            sql_results = [dict(row._mapping) for row in res.fetchall()]
        await engine.dispose()
    else:
        # Use the existing session's DB
        res = await db.execute(text(sql_query))
        sql_results = [dict(row._mapping) for row in res.fetchall()]

    # 7. Call LLM_API_SERVER_INTERPRETATION_URL
    interpretation_payload = {
        "sql_results": sql_results,
        "user_query": query,
        "query_type": "population"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            int_resp = await client.post(
                LLM_API_SERVER_INTERPRETATION_URL, 
                json=interpretation_payload, 
                headers=headers, 
                timeout=60.0
            )
            int_resp.raise_for_status()
            int_data = int_resp.json()
        except Exception as e:
            logger.error(f"Interpretation API failed: {e}")
            int_data = {"interpretation": "Error interpreting results", "images": []}

    # 8. Construct LlmResultData response
    # Extract person_ids from sql_results
    person_ids = []
    for row in sql_results:
        pid = row.get("person_id")
        if pid:
            person_ids.append(pid)
    
    # Convert person_ids to ModelCase objects
    patients = []
    for pid in person_ids:
        case = await get_model_case_by_person_id(db, pid, registry)
        if case:
            patients.append(case)

    return LlmResultData(
        query=query,
        queryType=type,
        interpretation=int_data.get("interpretation"),
        images=int_data.get("images", []),
        patients=patients
    )
