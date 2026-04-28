from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict

from .annotation import Annotation
from .manual_case_data import ManualCaseData

class UserFlagAnnotationManualData(BaseModel):
    annotations: Optional[List[Annotation]] = None
    flag: Optional[str] = None
    manualCaseData: Optional[List[ManualCaseData]] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )
