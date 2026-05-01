import os
from datetime import datetime
from typing import List, Optional, Dict

from fastapi import APIRouter, Path, Query, Depends, HTTPException, Body, Response
from sqlalchemy import text
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
    if remaining >= 3:
        result["system"] = parts[offset + 0]
        result["code"] = parts[offset + 1]
        result["display"] = parts[offset + 2]

    # Value handling:
    # - If we have exactly 5 parts: value is at index 4 (Format 3: datetime^system^code^display^value)
    # - If we have 6 or more parts: value is at index 4 (Format 3+ with unit or CodeableConcept)
    # - If we have fewer than 5 parts: no value field (Formats 1 and 2 have no explicit value)
    if len(parts) >= 5:
        result["value"] = parts[4]
    # For formats with fewer than 5 parts (1-4), no value field is expected per specification

    # Unit extraction - when we have at least 6 parts and the value (index 4) appears to be numeric
    if len(parts) >= 6:
        # Check if the value (parts[4]) is numeric to determine if parts[5] is a unit
        try:
            float(parts[4])
            result["unit"] = parts[5]
        except ValueError:
            # If value is not numeric, parts[5] might be part of a CodeableConcept display
            pass

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
    sql = text(f"""
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
    """)
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
# GET endpoint – retrieve case record
# ---------------------------------------------------------------------------
@router.get(
    "/registry-viewer-api/case-record/{registry}",
    response_model=CaseData,
    responses={
        200: {"description": "search results matching criteria"},
        400: {"model": Error, "description": "Bad request – invalid parameters"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"model": Error, "description": "Not Found"},
    },
)
async def get_case_record(
    registry: str = Path(..., description="Registry Path"),
    caseId: int = Query(..., description="case-id for the category"),
    sections: Optional[str] = Query(
        None, description="sections to query for the case-id"
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
    if section_list:
        # Build OR conditions for each section
        or_conditions = []
        section_params: Dict[str, str] = {}
        for i, section in enumerate(section_list):
            or_conditions.append(f"section = :section_{i}")
            section_params[f"section_{i}"] = section
        cat_sql = text(f"""
            SELECT concept_id, section, category, question
            FROM {VIEWER_SCHEMA}.category
            WHERE {' OR '.join(or_conditions)}
        """)
        cat_result = await db.execute(cat_sql, section_params)
    else:
        # No section filter
        cat_sql = text(f"""
            SELECT concept_id, section, category, question
            FROM {VIEWER_SCHEMA}.category
        """)
        cat_result = await db.execute(cat_sql, {})
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
        # Build OR conditions for each concept_id
        or_conditions = []
        concept_params: Dict[str, int] = {}
        for i, concept_id in enumerate(concept_ids):
            or_conditions.append(f"o.observation_concept_id = :concept_{i}")
            concept_params[f"concept_{i}"] = concept_id
        obs_filter_sql = " OR ".join(or_conditions)
        filter_params = concept_params

    obs_sql = text(f"""
        SELECT
            o.observation_id,
            o.observation_datetime,
            o.observation_concept_id,
            o.value_as_string,
            o.observation_source_value,
            c.concept_code,
            c.concept_name
        FROM {registry}.observation AS o
        JOIN {registry}.person AS p ON o.person_id = p.person_id
        JOIN {registry}.case_info AS ci ON p.person_id = ci.person_id
        LEFT JOIN {VOCAB_SCHEMA}.concept AS c ON o.observation_concept_id = c.concept_id
        WHERE ci.case_info_id = :case_id
    """)
    # If we have a filter, append it
    if filter_params:
        obs_sql = text(str(obs_sql) + " AND " + obs_filter_sql)
    # Add the case_id parameter
    filter_params["case_id"] = caseId
    obs_result = await db.execute(obs_sql, filter_params)
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
        section = meta.get("section")
        
        # Skip Demographics sections as per requirement
        if section == "Demographics":
            continue
            
        content = Content(
            contentId=observation_id,
            date=parsed.get("date"),
            category=meta.get("category"),
            section=section,
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
    person_sql = text(f"SELECT person_id FROM {registry}.case_info WHERE case_info_id = :case_id")
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
    def make_naive(dt: datetime) -> datetime:
        # Strip timezone info for naive timestamp without time zone columns
        return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt

    default_content_id = None  # Will hold observation_id from first manualCaseData upsert for annotation linking

    # Flag update (requires contentId) – update viewer.flag table
    if body.flag is not None and contentId is not None:
        # Delete existing flag for given case and content, then insert
        del_sql = text(f"""
            DELETE FROM {VIEWER_SCHEMA}.flag
            WHERE case_id = :case_id AND content_id = :content_id
        """)
        await db.execute(del_sql, {"case_id": caseId, "content_id": contentId})
        # Insert new flag
        ins_sql = text(f"""
            INSERT INTO {VIEWER_SCHEMA}.flag (case_id, content_id, flag, created)
            VALUES (:case_id, :content_id, :flag, CURRENT_TIMESTAMP)
        """)
        await db.execute(ins_sql, {"case_id": caseId, "content_id": contentId, "flag": body.flag})

    # Annotation deletions and insertions
    if body.annotations:
        for ann in body.annotations:
            # Delete existing annotation when annotationId is present and text is null/empty
            if ann.annotationId is not None and (ann.text is None or ann.text == ""):
                del_sql = text(f"""
                    DELETE FROM {VIEWER_SCHEMA}.annotation WHERE annotation_id = :ann_id
                """)
                await db.execute(del_sql, {"ann_id": ann.annotationId})
            # Insert new annotation when annotationId is absent and text is provided
            elif ann.annotationId is None and ann.text:
                # Use the first manualCaseData observation_id as content_id if available
                if default_content_id is not None:
                    ins_sql = text(f"""
                        INSERT INTO {VIEWER_SCHEMA}.annotation (
                            case_id, content_id, date, text, created
                        ) VALUES (
                            :case_id, :content_id, :date, :text, CURRENT_TIMESTAMP
                        ) RETURNING annotation_id;
                    """)
                    await db.execute(
                        ins_sql,
                        {"case_id": caseId, "content_id": default_content_id, "date": make_naive(ann.date), "text": ann.text},
                    )
                # If no default content yet, we cannot link annotation; skip (or could error)
                # For now, we skip silently.

            # Manual case data upserts
    if body.manualCaseData:
        for mcd in body.manualCaseData:
            # Get next observation_id by max+1 (not safe for concurrent inserts, but we have no sequence)
            max_id_sql = text(f"SELECT COALESCE(MAX(observation_id), 0) FROM {registry}.observation")
            max_result = await db.execute(max_id_sql)
            max_id = max_result.fetchone()[0]
            obs_id = max_id + 1
            upsert_sql = text(f"""
                INSERT INTO {registry}.observation (
                    observation_id,
                    person_id,
                    observation_concept_id,
                    observation_date,
                    observation_datetime,
                    observation_type_concept_id,
                    value_as_string,
                    observation_source_value
                ) VALUES (
                    :obs_id,
                    :person_id,
                    :concept_id,
                    :obs_date,
                    :obs_dt,
                    :type_concept_id,
                    :value,
                    :source_value
                )
                ON CONFLICT (observation_id) DO UPDATE SET
                    observation_date = EXCLUDED.observation_date,
                    observation_datetime = EXCLUDED.observation_datetime,
                    observation_concept_id = EXCLUDED.observation_concept_id,
                    observation_type_concept_id = EXCLUDED.observation_type_concept_id,
                    value_as_string = EXCLUDED.value_as_string,
                    observation_source_value = EXCLUDED.observation_source_value,
                    person_id = EXCLUDED.person_id
                RETURNING observation_id;
            """)
            naive_date = make_naive(mcd.date)
            result = await db.execute(
                upsert_sql,
                {
                    "obs_id": obs_id,
                    "person_id": person_id,
                    "concept_id": mcd.conceptId,
                    "obs_date": naive_date.date(),
                    "obs_dt": naive_date,
                    "type_concept_id": 36685765,
                    "value": mcd.value,
                    "source_value": mcd.value,
                },
            )
            row = result.fetchone()
            if row and default_content_id is None:
                default_content_id = row[0]

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
