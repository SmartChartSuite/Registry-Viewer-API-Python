from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

class Annotation(BaseModel):
    annotationId: Optional[int] = Field(None, alias="annotation_id")
    date: datetime
    text: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )
