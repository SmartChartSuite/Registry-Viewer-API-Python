from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class Metadata(BaseModel):
    name: str
    description: Optional[str] = None
    tag: str
    viewerConfig: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        orm_mode = True
