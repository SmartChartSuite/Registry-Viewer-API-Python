from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.responses import JSONResponse
from sqlalchemy import select, update, delete
from app.db.base import get_async_session
from app.db.models import Metadata as MetadataModel
from app.schemas.metadata import Metadata as MetadataSchema, Metadatas
from app.security.deps import require_scope, require_metadata_scope, get_current_user

router = APIRouter(
    prefix="/registry-viewer-api/metadata",
    tags=["metadata-api-controller"],

)

# READ endpoint – requires read:metadata scope
@router.get("", response_model=Metadatas,
            dependencies=[Security(get_current_user), Depends(require_metadata_scope("read"))])
async def get_metadata(session = Depends(get_async_session)):
    async with session as db:
        result = await db.execute(select(MetadataModel))
        records = result.scalars().all()
        return Metadatas(count=len(records), metadatas=records)

# WRITE endpoint – requires write:metadata scope
@router.put("", response_model=MetadataSchema,
            dependencies=[Security(get_current_user), Depends(require_metadata_scope("write"))])
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

# CREATE endpoint – requires write:metadata scope
@router.post(
    "",
    response_model=MetadataSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {
            "description": "Metadata with same tag already exists",
            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Metadata"}}},
        }
    },
    dependencies=[Security(get_current_user), Depends(require_metadata_scope("write"))],
)
async def create_metadata(
    metadata: MetadataSchema,
    session=Depends(get_async_session),
):
    async with session as db:
        # Check for duplicate tag
        dup_stmt = select(MetadataModel).where(MetadataModel.tag == metadata.tag)
        dup_res = await db.execute(dup_stmt)
        existing = dup_res.scalar_one_or_none()
        if existing:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content=MetadataSchema.from_orm(existing).model_dump(),
            )
        # Insert new record
        new_row = MetadataModel(
            name=metadata.name,
            description=metadata.description,
            tag=metadata.tag,
            viewer_config=metadata.viewerConfig,
        )
        db.add(new_row)
        await db.commit()
        await db.refresh(new_row)
        return new_row

# DELETE endpoint – requires write:metadata scope
@router.delete(
    "",
    response_model=MetadataSchema,
    responses={
        200: {"description": "Metadata entry successfully deleted", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Metadata"}}}},
        404: {"description": "Metadata entry not found", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        400: {"description": "Bad request – invalid parameters", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
    },
    dependencies=[Security(get_current_user), Depends(require_metadata_scope("write"))],
)
async def delete_metadata(tag: str, session=Depends(get_async_session)):
    """
    Delete a metadata record identified by its `tag` query parameter.
    Returns the deleted metadata object on success.
    """
    async with session as db:
        stmt = select(MetadataModel).where(MetadataModel.tag == tag)
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if not existing:
            raise HTTPException(status_code=404, detail="Metadata not found")
        # Capture object before deletion
        deleted = MetadataSchema.from_orm(existing)
        await db.execute(delete(MetadataModel).where(MetadataModel.tag == tag))
        await db.commit()
        return deleted
