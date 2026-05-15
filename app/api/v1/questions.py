import os
from fastapi import APIRouter, Path, Query, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_async_session
from app.schemas.question import Question
from app.security.deps import get_current_user
from app.schemas.metadata import Error
from app.config import API_BASE_PATH

# ---------------------------------------------------------------------------
# Configuration helpers – read env vars (already present elsewhere)
# ---------------------------------------------------------------------------
DATA_SCHEMA = os.getenv("DATA_SCHEMA")
SCD_DATA_SCHEMA = os.getenv("SCD_DATA_SCHEMA")
VIEWER_SCHEMA = os.getenv("VIEWER_SCHEMA")

router = APIRouter(
    tags=["questions-api-controller"],
)

# ---------------------------------------------------------------------------
# GET endpoint – retrieve questions for a section
# ---------------------------------------------------------------------------
@router.get(
    f"/{API_BASE_PATH}/questions/{{registry}}",
    response_model=list[Question],
    responses={
        200: {"description": "list of questions"},
        400: {"model": Error, "description": "Bad request – invalid parameters"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"model": Error, "description": "Not Found"},
    },
)
async def get_questions(
    registry: str = Path(..., description="Registry Path"),
    section: str = Query(..., description="section that we are interested"),
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
    # 2️⃣ Query category table for matching section
    # -------------------------------------------------------------------
    sql = text(f"""
        SELECT concept_id, section, category, question
        FROM {VIEWER_SCHEMA}.category
        WHERE section = :section
    """)
    result = await db.execute(sql, {"section": section})
    rows = result.fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail={"code": 404, "message": "no questions found for section"},
        )

    # -------------------------------------------------------------------
    # 3️⃣ Build response
    # -------------------------------------------------------------------
    questions = []
    for row in rows:
        questions.append(Question(
            conceptId=row[0],
            section=row[1],
            category=row[2],
            text=row[3]
        ))
    
    return questions