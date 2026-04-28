from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

class ManualCaseData(BaseModel):
    conceptId: int = Field(alias="concept_id")
    date: datetime
    value: str
    annotation_id: Optional[int] = None  # If provided, indicates an annotation operation
    text: Optional[str] = None           # If None with annotation_id → delete the annotation
    # Additional optional fields can be added here (e.g., unit)

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )
