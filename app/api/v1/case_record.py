import os
from typing import List, Optional, Dict

from fastapi import APIRouter, Path, Query, Depends, HTTPException, Body, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_async_session
from app.schemas.case_data import CaseData, Content, Value, Coding, DetailUserData
from app.schemas.manual_case_data import ManualCaseData
from app.schemas.user_flag_annotation_manual_data import UserFlagAnnotationManualData
from app.schemas.metadata import Error
from app.security.deps import get_current_user

# ---------------------------------------------------------------------------
# Configuration helpers – read env vars (already present elsewhere)
# ---------------------------------------------------------------------------
DATA_SCHEMA = os.getenv("DATA_SCHEMA")
SCD_DATA_SCHEMA = os.getenv("SCD_DATA_SCHEMA")
VIEWER_SCHEMA = os.getenv("VIEWER_SCHEMA")
VOCAB_SCHEMA = os.getenv("VOCABULARY_SCHEMA")

# Lower bound for observation_concept_id when no sections are supplied.
# The specification fixed this at 2_000_000_000.
MIN_OBSERVATION_CONCEPT_ID = 2_000_000_000

router = APIRouter()

# ---------------------------------------------------------------------------
# Utility: parse the caret (^) delimited observation.value_as_string
# ---------------------------------------------------------------------------
def parse_observation_value(raw: str) -> dict:
    """Parse a '^'-delimited observation.value_as_string.

    Returns a dict containing optional fields:
        date, system, code, display, value, unit
    The rules follow the specification provided by the user.
    """
    if not raw:
        return {}
    parts = raw.split('^')
    result: Dict[str, Optional[str]] = {}

    # If there are more than 3 parts, the first part is a date.
    offset = 1 if len(parts) > 3 else 0
    if offset:
        result["date"] = parts[0]

    remaining = len(parts) - offset
    # Cases for system/code/display
    if remaining == 3:
        result["system"] = parts[offset + 0]
        result["code"] = parts[offset + 1]
        result["display"] = parts[offset + 2]
    elif remaining > 3:
        # second part is system, third is code, fourth is display
        result["system"] = parts[offset + 1]
        result["code"] = parts[offset + 2]
        result["display"] = parts[offset + 3]

    # Value extraction – fifth part if at least 5 total values, else first
    if len(parts) >= 5:
        result["value"] = parts[4]
    else:
        # Use the first non‑date part as fallback value
        result["value"] = parts[offset] if parts else None

    # Unit – only when exactly 6 parts are present
    if len(parts) == 6:
        result["unit"] = parts[5]

    return result

# ---------------------------------------------------------------------------
# Helper: fetch DetailUserData for a batch of content IDs
# ---------------------------------------------------------------------------
async def fetch_details(
    db: AsyncSession,
    registry_schema: str,
    content_ids: List[int],
) -> Dict[int, List[DetailUserData]]:
    """Return a mapping content_id → list of DetailUserData.

    The query joins fact_relationship with observation (by fact_id_1) and filters on
    relationship_concept_id = 44818759.
    """
    if not content_ids:
        return {}

    # Build the query using raw SQL for clarity; SQLAlchemy Core could be used as well.
    sql = f"""
        SELECT
            fr.domain_concept_id_1,
            fr.fact_id_1,
            fr.domain_concept_id_2,
            fr.fact_id_2,
            fr.relationship_concept_id,
            o.observation_id AS content_id
        FROM {registry_schema}.fact_relationship AS fr
        JOIN {registry_schema}.observation AS o
          ON o.observation_id = fr.fact_id_1
        WHERE o.observation_id = ANY(:content_ids)
          AND fr.relationship_concept_id = 44818759;
    """
    result = await db.execute(
        sql,
        {"content_ids": content_ids},
    )
    rows = result.fetchall()

    mapping: Dict[int, List[DetailUserData]] = {}
    for row in rows:
        content_id = row[5]
        detail = DetailUserData(
            domainConceptId1=row[0],
            factId1=row[1],
            domainConceptId2=row[2],
            factId2=row[3],
            relationshipConceptId=row[4],
        )
        mapping.setdefault(content_id, []).append(detail)
    return mapping

# ---------------------------------------------------------------------------
# Main endpoint implementation
# ---------------------------------------------------------------------------
@router.get(
    "/registry-viewer-api/case-record/{registry}",
    response_model=CaseData,
    responses={
        200: {"description": "Case data retrieved"},
        400: {"model": Error, "description": "Invalid request"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"model": Error, "description": "Case not found"},
    },
)
async def get_case_record(
    registry: str = Path(..., description="Registry schema name"),
    caseId: int = Query(..., description="case‑id for the category"),
    sections: Optional[str] = Query(
        None, description="CSV list of section identifiers"
    ),
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
    # 2️⃣ Parse sections – produce a list or None
    # -------------------------------------------------------------------
    section_list: Optional[List[str]] = None
    if sections:
        # Split on commas and strip whitespace; ignore empty entries.
        section_list = [s.strip() for s in sections.split(',') if s.strip()]
        if not section_list:
            section_list = None

    # -------------------------------------------------------------------
    # 3️⃣ Load category mapping (concept_id → section/category/question)
    # -------------------------------------------------------------------
    cat_sql = f"""
        SELECT concept_id, section, category, question
        FROM {VIEWER_SCHEMA}.category
        WHERE (:section_list IS NULL OR section = ANY(:section_list))
    """
    cat_result = await db.execute(
        cat_sql,
        {"section_list": section_list},
    )
    cat_rows = cat_result.fetchall()
    # Build lookup dicts
    concept_to_meta: Dict[int, Dict[str, str]] = {}
    concept_ids: List[int] = []
    for row in cat_rows:
        cid = row[0]
        concept_ids.append(cid)
        concept_to_meta[cid] = {
            "section": row[1],
            "category": row[2],
            "question": row[3],
        }

    # -------------------------------------------------------------------
    # 4️⃣ Resolve observations with conditional concept filter
    # -------------------------------------------------------------------
    if not section_list:
        # No sections – filter by numeric lower bound
        obs_filter_sql = "o.observation_concept_id > :min_concept_id"
        filter_params = {"min_concept_id": MIN_OBSERVATION_CONCEPT_ID}
    else:
        # Sections provided – restrict to the concept IDs we just fetched
        obs_filter_sql = "o.observation_concept_id = ANY(:concept_ids)"
        filter_params = {"concept_ids": concept_ids}

    obs_sql = f"""
        SELECT
            o.observation_id,
            o.observation_datetime,
            o.observation_concept_id,
            o.vocabulary_id,
            o.value_as_string,
            o.observation_source_value,
            c.concept_code,
            c.concept_name,
            vt.system,
            vt.unit,
            vt.value
        FROM {registry}.observation AS o
        JOIN {registry}.person AS p ON o.person_id = p.person_id
        JOIN {registry}.case_info AS ci ON p.person_id = ci.person_id
        LEFT JOIN {VOCAB_SCHEMA}.concept AS c ON o.observation_concept_id = c.concept_id
        LEFT JOIN {VOCAB_SCHEMA}.concept AS vt ON o.observation_type_concept_id = vt.concept_id
        WHERE ci.case_id = :case_id
          AND ({obs_filter_sql})
    """
    obs_params = {"case_id": caseId, **filter_params}
    obs_result = await db.execute(obs_sql, obs_params)
    obs_rows = obs_result.fetchall()

    if not obs_rows:
        raise HTTPException(
            status_code=404,
            detail={"code": 404, "message": "case not found"},
        )

    # -------------------------------------------------------------------
    # 5️⃣ Build Content objects
    # -------------------------------------------------------------------
    contents: List[Content] = []
    content_ids: List[int] = []
    for row in obs_rows:
        observation_id = row[0]
        content_ids.append(observation_id)
        raw_value = row[4]  # value_as_string
        parsed = parse_observation_value(raw_value)

        # Build derivedValue (Value model)
        coding = None
        if parsed.get("system") or parsed.get("code") or parsed.get("display"):
            coding = Coding(
                system=parsed.get("system"),
                code=parsed.get("code"),
                display=parsed.get("display"),
            )
        derived = Value(
            coding=coding,
            unit=parsed.get("unit"),
            value=parsed.get("value"),
        )

        meta = concept_to_meta.get(row[2], {})  # row[2] is observation_concept_id
        content = Content(
            contentId=observation_id,
            date=parsed.get("date"),
            category=meta.get("category"),
            section=meta.get("section"),
            question=meta.get("question"),
            derivedValue=derived,
            # flag, sourceValue, etc. can be added later if needed.
        )
        contents.append(content)

    # -------------------------------------------------------------------
    # 6️⃣ Fetch DetailUserData for each content (batched)
    # -------------------------------------------------------------------
    details_map = await fetch_details(db, registry, content_ids)
    for content in contents:
        details = details_map.get(content.contentId)
        if not details:
            # Fallback – use derived value as tableDisplayText
            fallback = DetailUserData(
                tableDisplayText=content.derivedValue.value
            )
            content.details = [fallback]
        else:
            content.details = details

    # -------------------------------------------------------------------
    # 7️⃣ Assemble final response
    # -------------------------------------------------------------------
    case_data = CaseData(
        caseId=caseId,
        contents=contents,
        count=len(contents),
    )
    return case_data

# ---------------------------------------------------------------------------
# PUT endpoint – upsert ManualCaseData into observation table
# ---------------------------------------------------------------------------
@router.put(
    "/registry-viewer-api/case-record/{registry}",
    # No response body – only HTTP status
    response_model=None,
    responses={
        200: {"description": "Observation upserted / updated successfully"},
        201: {"description": "Observation created successfully"},
        400: {"model": Error, "description": "Invalid request"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"model": Error, "description": "Case not found"},
        409: {"description": "Conflict – duplicate observation_id"},
    },
)
async def put_case_record(
    registry: str = Path(..., description="Registry schema name"),
    caseId: int = Query(..., description="case‑id for the category"),
    contentId: Optional[int] = Query(None, description="contentId (optional, identifies content to update)"),
    body: UserFlagAnnotationManualData = Body(..., description="User flag, annotations, and manual case data"),
    db: AsyncSession = Depends(get_async_session),
    auth: dict = Depends(get_current_user),
):
    # -----------------------------------------------------------------
    # 1️⃣ Validate registry name
    # -----------------------------------------------------------------
    if registry not in {DATA_SCHEMA, SCD_DATA_SCHEMA}:
        raise HTTPException(
            status_code=400,
            detail={"code": 400, "message": "invalid registry name"},
        )

    # -----------------------------------------------------------------
    # 2️⃣ Verify write scope (optional – here we just ensure auth works)
    # -----------------------------------------------------------------
    # Scope enforcement can be added via require_scope("write") if needed.

    # -----------------------------------------------------------------
    # 3️⃣ Resolve person_id for the given caseId
    # -----------------------------------------------------------------
    person_sql = f"SELECT person_id FROM {registry}.case_info WHERE case_id = :case_id"
    person_res = await db.execute(person_sql, {"case_id": caseId})
    person_row = person_res.fetchone()
    if not person_row:
        raise HTTPException(
            status_code=404,
            detail={"code": 404, "message": "case not found"},
        )
    person_id = person_row[0]

    # -----------------------------------------------------------------
    # 4️⃣ Process flags, annotations, and manual case data
    # -----------------------------------------------------------------
    # Flag update (requires contentId)
    if body.flag is not None and contentId is not None:
        flag_sql = f"""
            UPDATE {registry}.observation
            SET flag = :flag
            WHERE observation_id = :obs_id
        """
        await db.execute(flag_sql, {"flag": body.flag, "obs_id": contentId})

    # Annotation deletions
    if body.annotations:
        for ann in body.annotations:
            # Delete existing annotation when annotationId is present and text is null/empty
            if ann.annotationId is not None and (ann.text is None or ann.text == ""):
                del_sql = f"""
                    DELETE FROM {registry}.annotation WHERE annotation_id = :ann_id
                """
                await db.execute(del_sql, {"ann_id": ann.annotationId})
            # Insert new annotation when annotationId is absent and text is provided
            elif ann.annotationId is None and ann.text:
                ins_sql = f"""
                    INSERT INTO {registry}.annotation (
                        date,
                        text
                    ) VALUES (
                        :date,
                        :text
                    ) RETURNING annotation_id;
                """
                await db.execute(
                    ins_sql,
                    {"date": ann.date, "text": ann.text},
                )

    # Manual case data upserts
    if body.manualCaseData:
        for mcd in body.manualCaseData:
            upsert_sql = f"""
                INSERT INTO {registry}.observation (
                    observation_datetime,
                    observation_concept_id,
                    observation_type_concept_id,
                    value_as_string,
                    observation_source_value,
                    person_id
                ) VALUES (
                    :obs_dt,
                    :concept_id,
                    :type_concept_id,
                    :value,
                    :source_value,
                    :person_id
                )
                ON CONFLICT (observation_id) DO UPDATE SET
                    observation_datetime = EXCLUDED.observation_datetime,
                    observation_concept_id = EXCLUDED.observation_concept_id,
                    observation_type_concept_id = EXCLUDED.observation_type_concept_id,
                    value_as_string = EXCLUDED.value_as_string,
                    observation_source_value = EXCLUDED.observation_source_value,
                    person_id = EXCLUDED.person_id
                RETURNING observation_id;
            """
            await db.execute(
                upsert_sql,
                {
                    "obs_dt": mcd.date,
                    "concept_id": mcd.conceptId,
                    "type_concept_id": 36685765,
                    "value": mcd.value,
                    "source_value": mcd.value,
                    "person_id": person_id,
                },
            )
    # Commit all changes
    await db.commit()

    # -----------------------------------------------------------------
    # 5️⃣ Return appropriate HTTP status (no body)
    # -----------------------------------------------------------------
    # Determine if any new observations were created.  We treat the presence
    # of at least one ManualCaseData entry as a creation operation.
    if body.manualCaseData:
        return Response(status_code=201)
    return Response(status_code=200)
