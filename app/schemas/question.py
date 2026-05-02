from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class Question(BaseModel):
    conceptId: int = Field(alias="concept_id")
    section: str
    category: str
    text: str

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )