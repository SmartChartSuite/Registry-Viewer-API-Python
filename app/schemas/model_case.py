from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from .metadata import Status

class ModelCase(BaseModel):
    caseId: int = Field(alias="case_id")
    city: Optional[str] = None
    dob: Optional[str] = None  # Date of birth as string (format: date)
    firstName: Optional[str] = None
    gender: Optional[str] = None
    initialReportDate: Optional[str] = None  # Date-time string
    lastName: Optional[str] = None
    phone: Optional[str] = None
    state: Optional[str] = None
    status: Optional[Status] = None
    street: Optional[str] = None
    zip: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

# Rebuild schema to resolve forward references
ModelCase.model_rebuild()