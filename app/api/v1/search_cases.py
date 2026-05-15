import os
import re
from fastapi import APIRouter, Path, Query, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.base import get_async_session
from app.schemas.model_case import ModelCase
from app.schemas.case_data import Cases
from app.security.deps import get_current_user
from app.schemas.metadata import Error, Status
from app.config import API_BASE_PATH

# ---------------------------------------------------------------------------
# Configuration helpers – read env vars (already present elsewhere)
# ---------------------------------------------------------------------------
DATA_SCHEMA = os.getenv("DATA_SCHEMA")
SCD_DATA_SCHEMA = os.getenv("SCD_DATA_SCHEMA")
VOCABULARY_SCHEMA = os.getenv("VOCABULARY_SCHEMA")

router = APIRouter(
    tags=["search-cases-api-controller"],
)

# ---------------------------------------------------------------------------
# GET endpoint – search cases
# ---------------------------------------------------------------------------
@router.get(
    f"/{API_BASE_PATH}/search-cases/{{registry}}",
    response_model=Cases,
    responses={
        200: {"description": "Search results matching criteria"},
        400: {"model": Error, "description": "Bad request – invalid parameters"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"model": Error, "description": "Not Found"},
    },
)
async def search_cases(
    registry: str = Path(..., description="Registry Path"),
    terms: Optional[str] = Query(None, description="search terms for cases"),
    fields: Optional[str] = Query(None, description="search columns for cases"),
    db: AsyncSession = Depends(get_async_session),
    auth: dict = Depends(get_current_user),
):
    # -------------------------------------------------------------------
    # 1️⃣ Validate registry name
    # -------------------------------------------------------------------
    if registry not in {DATA_SCHEMA, SCD_DATA_SCHEMA}:
        raise HTTPException(
            status_code=400,
            detail={"code": 400, "message": "invalid registry name"},
        )

    # -------------------------------------------------------------------
    # 2️⃣ Parse search terms and fields
    # -------------------------------------------------------------------
    search_terms: List[str] = []
    if terms:
        # Split by comma and trim whitespace
        search_terms = [term.strip() for term in terms.split(',') if term.strip()]
    
    search_fields: List[str] = []
    if fields:
        # Split by comma and trim whitespace
        search_fields = [field.strip() for field in fields.split(',') if field.strip()]
    
    # If no fields specified, search all fields
    if not search_fields:
        search_fields = [
            "family_name", "given1_name", "given2_name", "gender_concept_name", 
            "address_1", "address_2", "city", "state", "zip", "status"
        ]
    
    # -------------------------------------------------------------------
    # 3️⃣ Build the search query
    # -------------------------------------------------------------------
    # Base query joining the required tables
    base_sql = f"""
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
        LEFT JOIN {registry}.location AS loc ON p.location_id = loc.location_id
        LEFT JOIN {VOCABULARY_SCHEMA}.concept AS c ON p.gender_concept_id = c.concept_id
    """
    
    # Build WHERE clause for search terms
    where_conditions = []
    params = {}
    
    if search_terms:
        term_conditions = []
        for i, term in enumerate(search_terms):
            # Parse search method (exact:, begin:, end:) or default to contains
            method = "contains"  # default
            search_term = term
            
            if ':' in term:
                parts = term.split(':', 1)
                search_term = parts[0]  # First part is the search term
                method = parts[1].lower() if len(parts) > 1 and parts[1] else "contains"  # Second part is the method
            
            # If method is empty after parsing, default to contains
            if not method:
                method = "contains"
            
            # Build condition for each field
            field_conditions = []
            for field in search_fields:
                param_name = f"term_{i}_{field}"
                field_conditions.append(f"LOWER({field}) {get_search_operator(method)} :{param_name}")
                params[param_name] = get_search_value(method, search_term)
            
            if field_conditions:
                term_conditions.append(f"({' OR '.join(field_conditions)})")
        
        if term_conditions:
            where_conditions.append(f"({' OR '.join(term_conditions)})")
    
    # Construct final query
    final_sql = base_sql
    if where_conditions:
        final_sql += " WHERE " + " AND ".join(where_conditions)
    
    # -------------------------------------------------------------------
    # 4️⃣ Execute query and build response
    # -------------------------------------------------------------------
    result = await db.execute(text(final_sql), params)
    rows = result.fetchall()
    
    if not rows:
        # Return empty results rather than 404 for search endpoints
        return Cases(case=[], count=0)
    
    # Build ModelCase objects
    cases = []
    for row in rows:
        # Parse date of birth components
        dob = None
        if row[11] is not None and row[12] is not None and row[13] is not None:  # year, month, day
            try:
                year = int(row[11])
                month = int(row[12]) if row[12] else 1
                day = int(row[13]) if row[13] else 1
                dob = f"{year:04d}-{month:02d}-{day:02d}"
            except (ValueError, TypeError):
                dob = None
        
        # Combine address lines
        street_parts = []
        if row[17]:  # address_1
            street_parts.append(str(row[17]))
        if row[18]:  # address_2
            street_parts.append(str(row[18]))
        street = " ".join(street_parts) if street_parts else None
        
        # Get phone number from any of the contact points (prioritize contact_point1).
        # Each contact_point is a : delimited value. If the first part is "phone" or "mobile", 
        # then we can treat the third part as the phone number. 
        # Otherwise, we check if conteact_phone2 or contact_phone3 has a valid phone number. 
        phone = None
        for contact_point in [row[14], row[15], row[16]]:  # contact_point1, contact_point2, contact_point3
            if contact_point:
                parts = contact_point.split(':')
                if len(parts) >= 3 and parts[0].lower() in {"phone", "mobile"}:
                    phone = parts[2].strip()
                    break
        
        # Build status object with mapping from database status code to UI code and description
        status_obj = None
        if row[22]:  # status
            from app.schemas.metadata import Status
            # Map database status code to UI code and description
            # Key is code_string (RUNNING, END, etc.), hex_code is reference value
            status_mapping = {
                "RUNNING": {
                    "hex_code": "0x0001",
                    "code_description": "Case is running for case monitoring.",
                    "ui_code": "information",
                    "ui_description": "Case is running in normal mode."
                },
                "END": {
                    "hex_code": "0x0002",
                    "code_description": "Case is at the end of active monitoring period.",
                    "ui_code": "information",
                    "ui_description": "Case is outside of monitoring period and not tracked."
                },
                "REQUEST_PENDING": {
                    "hex_code": "0x0004",
                    "code_description": "Request to Query for case is queued but not yet in running queue.",
                    "ui_code": "information",
                    "ui_description": "Job is pending. The number of allowed concurrent jobs can be configured."
                },
                "TIMED_OUT": {
                    "hex_code": "0x0008",
                    "code_description": "Retry count reached the maximum allowed count. Giving up.",
                    "ui_code": "timed-out",
                    "ui_description": "Job taking longer than expected. This may indicate a temporary network error. If this error persists, please contact technical support. (0x0008)."
                },
                "PAUSED": {
                    "hex_code": "0x0010",
                    "code_description": "Case is paused by system admin.",
                    "ui_code": "paused",
                    "ui_description": "Case is paused by system administrator. (0x0010)"
                },
                "ERROR_IN_CLIENT": {
                    "hex_code": "0x0100",
                    "code_description": "Error occurred on client side during Request. Request is paused.",
                    "ui_code": "fatal",
                    "ui_description": "Registry internal error occurred. Please contact technical support (0x0100)."
                },
                "ERROR_IN_SERVER": {
                    "hex_code": "0x0200",
                    "code_description": "Error occurred on server side during Request. Request will be made again until it reaches the maximum retry-count.",
                    "ui_code": "fatal",
                    "ui_description": "Registry encountered an error in the backend services. Please contact technical support (0x0200)."
                },
                "RESULT_PARSE_ERROR": {
                    "hex_code": "0x0201",
                    "code_description": "Error occurred when parsing the server response data",
                    "ui_code": "fatal",
                    "ui_description": "Registry encountered an error with Data Received from provider. Please contact technical support (0x0201)."
                },
                "ERROR_UNKNOWN": {
                    "hex_code": "0x0400",
                    "code_description": "Unknown error occurred. Some resources in result bundle failed to be imported to db.",
                    "ui_code": "error",
                    "ui_description": "Error occurred during data import to registry. Please contact technical support (0x0400)"
                },
                "INVALID": {
                    "hex_code": "0x0000",
                    "code_description": "Invalid Status. Retrigger with a valid status is required.",
                    "ui_code": "warning",
                    "ui_description": "not in use (0x0000)"
                }
            }
            
            # Get status string from database (should be code_string like "RUNNING", "END", etc.)
            db_status_string = str(row[22]).strip()
            
            # Look up in mapping using code_string as key
            status_info = status_mapping.get(db_status_string, {
                "hex_code": "unknown",
                "code_description": f"Unknown status code: {db_status_string}",
                "ui_code": "unknown",
                "ui_description": f"Unknown status code: {db_status_string}"
            })
            
            status_obj = Status(
                activatedDateTime=row[1].isoformat() if row[1] else None,  # activated_datetime
                caseStartedRunningDateTime=row[6].isoformat() if row[6] else None,  # case_started_running_datetime
                code=status_info["ui_code"],  # Maps to Status.code
                createdDateTime=row[2].isoformat() if row[2] else None,  # created_datetime
                detail=status_info["ui_description"],  # Maps to Status.detail
                lastSuccessfulDateTime=row[5].isoformat() if row[5] else None,  # last_successful_datetime
                nextScheduledDateTime=row[3].isoformat() if row[3] else None  # trigger_at_datetime (last_trigger_at_datetime)
            )
        
        case = ModelCase(
            caseId=row[0],  # case_info_id
            city=row[19],   # city
            dob=dob,        # date of birth
            firstName=row[8],  # given1_name
            gender=row[10],   # gender_concept_name
            initialReportDate=row[1].isoformat() if row[1] else None,  # activated_datetime
            lastName=row[7],   # family_name
            phone=phone,
            state=row[20],     # state
            status=status_obj,
            street=street,
            zip=row[21]        # zip
        )
        cases.append(case)
    
    return Cases(case=cases, count=len(cases))

def get_search_operator(method: str) -> str:
    """Get SQL operator based on search method"""
    method = method.lower()
    if method == "exact":
        return "="
    elif method == "begin":
        return "LIKE"
    elif method == "end":
        return "LIKE"
    else:  # contains or default
        return "LIKE"

def get_search_value(method: str, term: str) -> str:
    """Get search value based on search method"""
    method = method.lower()
    if method == "exact":
        return term.lower()
    elif method == "begin":
        return f"{term.lower()}%"
    elif method == "end":
        return f"%{term.lower()}"
    else:  # contains or default
        return f"%{term.lower()}%"