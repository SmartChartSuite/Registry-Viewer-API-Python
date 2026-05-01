import os
from datetime import datetime
from typing import List, Optional, Dict, Union

from fastapi import APIRouter, Path, Query, Depends, HTTPException, Body, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_async_session
from app.schemas.case_data import CaseData, Content, Value, Coding, DetailUserData, DetailMedication, DetailObservation, DetailNote, DetailCondition, DetailMeasurement
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
# Helper: fetch details for a batch of content IDs with conditional logic based on domain_concept_id_2
# ---------------------------------------------------------------------------
async def fetch_details(
    db: AsyncSession,
    registry_schema: str,
    content_ids: List[int],
) -> Dict[int, List[Union[DetailUserData, DetailMedication, DetailObservation, DetailNote, DetailCondition, DetailMeasurement]]]:
    """Return a mapping content_id → list of detail objects based on domain_concept_id_2.

    For each content_id, fetches related fact_relationship rows and maps them to appropriate detail schemas:
    - If no facts: fallback to DetailUserData with derivedValue as tableDisplayText
    - domain_concept_id_2 = 13 → DetailMedication (drug_exposure + concept joins)
    - domain_concept_id_2 = 19 → DetailCondition (condition_occurrence + concept join)
    - domain_concept_id_2 = 27 → DetailObservation (observation + concept joins)
    - domain_concept_id_2 = 21 → DetailMeasurement (measurement + concept joins)
    - domain_concept_id_2 = 5085 → DetailNote (note + concept join)
    - Other values: skip
    """
    if not content_ids:
        return {}

    # Build the query to get all relevant fact_relationship rows
    sql = text(f"""
        SELECT
            fr.domain_concept_id_1,
            fr.fact_id_1,
            fr.domain_concept_id_2,
            fr.fact_id_2,
            fr.relationship_concept_id
        FROM {registry_schema}.fact_relationship AS fr
        WHERE fr.fact_id_1 = ANY(:content_ids)
          AND fr.relationship_concept_id = 44818759;
    """)
    result = await db.execute(
        sql,
        {"content_ids": content_ids},
    )
    rows = result.fetchall()

    # Group facts by content_id (fact_id_1)
    facts_by_content: Dict[int, List[Dict]] = {}
    for row in rows:
        content_id = row[1]  # fact_id_1
        fact_dict = {
            "domain_concept_id_1": row[0],
            "fact_id_1": row[1],
            "domain_concept_id_2": row[2],
            "fact_id_2": row[3],
            "relationship_concept_id": row[4],
        }
        facts_by_content.setdefault(content_id, []).append(fact_dict)

    # Process each content_id
    mapping: Dict[int, List[Union[DetailUserData, DetailMedication, DetailObservation, DetailNote, DetailCondition, DetailMeasurement]]] = {}
    
    for content_id in content_ids:
        facts = facts_by_content.get(content_id, [])
        
        if not facts:
            # No facts found - this will be handled in the calling function with derivedValue fallback
            mapping[content_id] = []
            continue
            
        details: List[Union[DetailUserData, DetailMedication, DetailObservation, DetailNote, DetailCondition, DetailMeasurement]] = []
        
        for fact in facts:
            domain_concept_id_2 = fact["domain_concept_id_2"]
            fact_id_2 = fact["fact_id_2"]
            
            # Route to appropriate detail handler based on domain_concept_id_2
            if domain_concept_id_2 == 13:
                # DetailMedication
                detail = await _get_medication_detail(db, registry_schema, fact_id_2)
                if detail:
                    details.append(detail)
            elif domain_concept_id_2 == 19:
                # DetailCondition
                detail = await _get_condition_detail(db, registry_schema, fact_id_2)
                if detail:
                    details.append(detail)
            elif domain_concept_id_2 == 27:
                # DetailObservation
                detail = await _get_observation_detail(db, registry_schema, fact_id_2)
                if detail:
                    details.append(detail)
            elif domain_concept_id_2 == 21:
                # DetailMeasurement
                detail = await _get_measurement_detail(db, registry_schema, fact_id_2)
                if detail:
                    details.append(detail)
            elif domain_concept_id_2 == 5085:
                # DetailNote
                detail = await _get_note_detail(db, registry_schema, fact_id_2)
                if detail:
                    details.append(detail)
            # Other domain_concept_id_2 values are skipped as per requirements
            
        mapping[content_id] = details
        
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
        raw_value = row[3]  # value_as_string
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
            
        # Parse observation_source_value the same way as observation.value_as_string
        source_value_parsed = parse_observation_value(row[4])  # row[4] is observation_source_value
        source_value_coding = None
        if source_value_parsed.get("system") or source_value_parsed.get("code") or source_value_parsed.get("display"):
            source_value_coding = Coding(
                system=source_value_parsed.get("system"),
                code=source_value_parsed.get("code"),
                display=source_value_parsed.get("display"),
            )
        source_value = Value(
            coding=source_value_coding,
            unit=source_value_parsed.get("unit"),
            value=source_value_parsed.get("value"),
        )

        content = Content(
            contentId=observation_id,
            date=parsed.get("date"),
            category=meta.get("category"),
            section=section,
            question=meta.get("question"),
            derivedValue=derived,
            sourceValue=source_value,
            # flag, etc. can be added later if needed.
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

# ---------------------------------------------------------------------------
# Helper methods for detail type extraction
# ---------------------------------------------------------------------------
async def _get_medication_detail(
    db: AsyncSession,
    registry_schema: str,
    drug_exposure_id: int,
) -> Optional[DetailMedication]:
    """Fetch medication detail by joining drug_exposure with concept tables."""
    sql = text(f"""
        SELECT
            de.drug_exposure_id,
            de.days_supply,
            de.lot_number,
            de.quantity,
            de.refills,
            c_drug.concept_code AS drug_code,
            c_drug.concept_name AS drug_display,
            c_drug.vocabulary_id AS drug_system,
            c_route.concept_code AS route_code,
            c_route.concept_name AS route_display,
            c_route.vocabulary_id AS route_system,
            de.sig,
            de.drug_exposure_start_date AS start_date
        FROM {registry_schema}.drug_exposure AS de
        JOIN {VOCAB_SCHEMA}.concept AS c_drug
            ON de.drug_concept_id = c_drug.concept_id
        LEFT JOIN {VOCAB_SCHEMA}.concept AS c_route
            ON de.route_concept_id = c_route.concept_id
        WHERE de.drug_exposure_id = :drug_exposure_id
    """)
    result = await db.execute(sql, {"drug_exposure_id": drug_exposure_id})
    row = result.fetchone()
    if not row:
        return None
        
    table_display_text = f"{row[6]}" if row[6] else None
    
    return DetailMedication(
        code=row[5],  # route_code
        display=row[6],  # route_display
        system=row[7],  # route_system
        startDate=row[12].isoformat() if row[12] else None,
        daysSupply=row[1],
        lotNumber=row[2],
        quantity=row[3],
        refills=row[4],
        route_code=row[8],
        route_display=row[9],
        route_system=row[10],
        sig=row[11],
        tableDisplayText=table_display_text,
    )


async def _get_condition_detail(
    db: AsyncSession,
    registry_schema: str,
    condition_occurrence_id: int,
) -> Optional[DetailCondition]:
    """Fetch condition detail by joining condition_occurrence with concept table."""
    sql = text(f"""
        SELECT
            co.condition_occurrence_id,
            co.condition_start_date,
            co.condition_end_date,
            co.condition_type_concept_id,
            c.concept_code,
            c.concept_name,
            c.vocabulary_id
        FROM {registry_schema}.condition_occurrence AS co
        JOIN {VOCAB_SCHEMA}.concept AS c
            ON co.condition_concept_id = c.concept_id
        WHERE co.condition_occurrence_id = :condition_occurrence_id
    """)
    result = await db.execute(sql, {"condition_occurrence_id": condition_occurrence_id})
    row = result.fetchone()
    if not row:
        return None
        
    # Build tableDisplayText: concept_name: concept_code
    table_display_text = f"{row[5]}: {row[4]}" if row[4] and row[5] else None
    
    return DetailCondition(
        code=row[4],  # concept_code
        display=row[5],  # concept_name
        system=row[6],  # vocabulary_id
        startDate=row[1].isoformat() if row[1] else None,
        endDate=row[2].isoformat() if row[2] else None,
        tableDisplayText=table_display_text,
    )


async def _get_observation_detail(
    db: AsyncSession,
    registry_schema: str,
    observation_id: int,
) -> Optional[DetailObservation]:
    """Fetch observation detail with concept names for tableDisplayText."""
    sql = text(f"""
        SELECT
            o.observation_id,
            o.unit_as_string,
            o.value_as_string,
            c_obs.concept_name AS observation_concept_name,
            c_value.concept_name AS value_as_concept_name,
            o.value_as_number,
            o.unit_as_string
        FROM {registry_schema}.observation AS o
        JOIN {VOCAB_SCHEMA}.concept AS c_obs
            ON o.observation_concept_id = c_obs.concept_id
        LEFT JOIN {VOCAB_SCHEMA}.concept AS c_value
            ON o.value_as_concept_id = c_value.concept_id
        WHERE o.observation_id = :observation_id
    """)
    result = await db.execute(sql, {"observation_id": observation_id})
    row = result.fetchone()
    if not row:
        return None
        
    # Build tableDisplayText per requirements
    table_display_parts = []
    
    # Add value_as_concept_name if exists
    if row[4]:  # value_as_concept_name
        table_display_parts.append(row[4])
    
    # Always add observation concept name
    if row[3]:  # observation_concept_name
        table_display_parts.append(row[3])
    
    # Add value_as_number and unit if value_as_number exists
    if row[5] is not None:  # value_as_number
        table_display_parts.append(str(row[5]))
        if row[6]:  # unit
            table_display_parts.append(row[6])
    
    # Add value_as_string if exists
    if row[2]:  # value_as_string
        table_display_parts.append(row[2])
    
    table_display_text = " | ".join(table_display_parts) if table_display_parts else None
    
    return DetailObservation(
        code=None,  # Not applicable for observation detail
        display=row[4] or row[3],  # value_as_concept_name or observation_concept_name
        system=None,  # Not applicable for observation detail
        startDate=None,  # Not applicable for observation detail
        endDate=None,  # Not applicable for observation detail
        tableDisplayText=table_display_text,
        unit=row[1],  # unit_as_string
        value=row[2],  # value_as_string
    )


async def _get_note_detail(
    db: AsyncSession,
    registry_schema: str,
    note_id: int,
) -> Optional[DetailNote]:
    """Fetch note detail by joining note with concept table."""
    sql = text(f"""
        SELECT
            n.note_id,
            n.note_text,
            c.concept_code,
            c.concept_name,
            c.vocabulary_id
        FROM {registry_schema}.note AS n
        JOIN {VOCAB_SCHEMA}.concept AS c
            ON n.note_type_concept_id = c.concept_id
        WHERE n.note_id = :note_id
    """)
    result = await db.execute(sql, {"note_id": note_id})
    row = result.fetchone()
    if not row:
        return None
        
    return DetailNote(
        code=row[2],  # concept_code
        display=row[3],  # concept_name
        system=row[4],  # vocabulary_id
        startDate=None,  # Not applicable for note detail
        endDate=None,  # Not applicable for note detail
        tableDisplayText=row[1],  # note_text
        noteText=row[1],
    )


async def _get_measurement_detail(
    db: AsyncSession,
    registry_schema: str,
    measurement_id: int,
) -> Optional[DetailMeasurement]:
    """Fetch measurement detail with concept names for tableDisplayText."""
    sql = text(f"""
        SELECT
            m.measurement_id,
            m.range_high,
            m.range_low,
            m.unit_concept_id,
            m.value_source_value,
            m.value_as_number,
            m.operator_concept_id,
            m.measurement_date,
            c_meas.concept_name AS measurement_concept_name,
            c_value.concept_name AS value_as_concept_name,
            c_unit.concept_name AS unit_concept_name,
            c_operator.concept_name AS operator_concept_name
        FROM {registry_schema}.measurement AS m
        JOIN {VOCAB_SCHEMA}.concept AS c_meas
            ON m.measurement_concept_id = c_meas.concept_id
        LEFT JOIN {VOCAB_SCHEMA}.concept AS c_value
            ON m.value_as_concept_id = c_value.concept_id
        LEFT JOIN {VOCAB_SCHEMA}.concept AS c_unit
            ON m.unit_concept_id = c_unit.concept_id
        LEFT JOIN {VOCAB_SCHEMA}.concept AS c_operator
            ON m.operator_concept_id = c_operator.concept_id
        WHERE m.measurement_id = :measurement_id
    """)
    result = await db.execute(sql, {"measurement_id": measurement_id})
    row = result.fetchone()
    if not row:
        return None
        
    # Build tableDisplayText per requirements
    table_display_parts = []
    
    measurement_value = None

    # Add value_as_concept_name if exists
    if row[9]:  # value_as_concept_name
        table_display_parts.append(row[9])   
    elif row[5] is not None:  # Add value_as_number with operator concept name if exists
        if row[11]:  # operator_concept_name
            table_display_parts.append(f"{row[11]} {row[5]}")
            measurement_value = f"{row[11]} {row[5]}"
        else:
            table_display_parts.append(str(row[5]))
            measurement_value = str(row[5])
        
        # Add unit if exists
        if row[10]:  # unit_concept_name
            table_display_parts.append(row[10])
    elif row[4]:  # value_source_value
        table_display_parts.append(row[4])
        measurement_value = row[4]
            
    table_display_text = " | ".join(table_display_parts) if table_display_parts else None
    
    # Determine display value
    display_value = None
    if row[9]:  # value_as_concept_name
        display_value = row[9]
    elif row[11] and row[5] is not None:  # operator_concept_name and value_as_number
        display_value = f"{row[11]} {row[5]}"
    elif row[5] is not None:  # value_as_number only
        display_value = str(row[5])
    elif row[4]:  # value_source_value
        display_value = row[4]
    
    # Get unit from unit concept name
    unit_value = row[10] if row[10] else None
    
    return DetailMeasurement(
        code=None,  # Not applicable for measurement detail
        date=row[7].isoformat() if row[7] else None,  # measurement_date
        display=display_value,
        system=None,  # Not applicable for measurement detail
        endDate=None,  # Not applicable for measurement detail
        tableDisplayText=table_display_text,
        rangeHigh=row[1],  # range_high
        rangeLow=row[2],   # range_low
        unit=unit_value,   # unit_concept_name
        value=measurement_value,      # value_source_value
    )
