from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, update
from app.db.base import get_async_session
from app.db.models import Metadata as MetadataModel
from app.schemas.metadata import Metadata as MetadataSchema
from app.security.deps import require_scope

router = APIRouter(
    prefix="/registry-viewer-api/metadata",
    tags=["metadata-api-controller"],
)

# READ endpoint – requires read:metadata scope
@router.get("/", response_model=MetadataSchema,
            dependencies=[Depends(require_scope("read"))])
async def get_metadata(tag: str = Query(..., description="Registry tag to look up"),
                       session = Depends(get_async_session)):
    async with session as db:
        result = await db.execute(select(MetadataModel).where(MetadataModel.tag == tag))
        record = result.scalar_one_or_none()
        if not record:
            raise HTTPException(status_code=404, detail="Metadata not found")
        return record

# WRITE endpoint – requires write:metadata scope
@router.put("/", response_model=MetadataSchema,
            dependencies=[Depends(require_scope("write"))])
async def update_metadata(metadata: MetadataSchema,
                          session = Depends(get_async_session)):
    async with session as db:
        stmt = (
            update(MetadataModel)
            .where(MetadataModel.tag == metadata.tag)
            .values(
                name=metadata.name,
                description=metadata.description,
                viewer_config=metadata.viewerConfig,
            )
            .returning(MetadataModel)
        )
        result = await db.execute(stmt)
        await db.commit()
        updated = result.fetchone()
        if not updated:
            raise HTTPException(status_code=404, detail="Metadata not found")
        return updated
