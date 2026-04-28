from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List

class Metadata(BaseModel):
    name: str
    description: Optional[str] = None
    tag: str
    # Map ORM attribute `viewer_config` to camelCase `viewerConfig` in JSON
    viewerConfig: Optional[Dict[str, Any]] = Field(default_factory=dict, alias="viewer_config")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# Response schema for GET /metadata (list of metadata entries)
class Error(BaseModel):
    code: int
    message: str

    model_config = ConfigDict(from_attributes=True)

class Metadatas(BaseModel):
    count: int
    metadatas: List[Metadata]
    version: str = "1.0.0"

    model_config = ConfigDict(from_attributes=True)
