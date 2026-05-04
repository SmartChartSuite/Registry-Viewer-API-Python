from __future__ import annotations

from typing import List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Basic coding representation – mirrors the OpenAPI Coding schema
# ---------------------------------------------------------------------------
class Coding(BaseModel):
    code: Optional[str] = None
    display: Optional[str] = None
    system: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# ---------------------------------------------------------------------------
# Value wrapper – contains an optional coding, unit and raw value string
# ---------------------------------------------------------------------------
class Value(BaseModel):
    coding: Optional[Coding] = None
    unit: Optional[str] = None
    value: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# ---------------------------------------------------------------------------
# Detail schemas – Updated to match OpenAPI spec DetailBase definition
# ---------------------------------------------------------------------------
class DetailBase(BaseModel):
    code: Optional[str] = Field(None, example="20507-0")
    display: Optional[str] = Field(None, example="Reagin Ab [Presence] in Serum by RPR")
    startDate: Optional[str] = Field(None, example="2022-01-14T05:00:00Z")
    endDate: Optional[str] = Field(None, example="2022-01-14T05:00:00Z")
    system: Optional[str] = Field(None, example="LOINC")
    tableDisplayText: Optional[str] = Field(None, example="Reagin Ab [Presence] in Serum by RPR | value")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

class DetailUserData(DetailBase):
    """Concrete detail type used when no fact_relationship rows exist.
    It inherits all fields from DetailBase and may only set tableDisplayText.
    """
    pass


# ---------------------------------------------------------------------------
# DetailMedication schema
# ---------------------------------------------------------------------------
class DetailMedication(DetailBase):
    daysSupply: Optional[int] = None
    lotNumber: Optional[str] = None
    quantity: Optional[int] = None
    refills: Optional[int] = None
    routeCode: Optional[str] = Field(None, alias="route_code")
    routeDisplay: Optional[str] = Field(None, alias="route_display")
    routeSystem: Optional[str] = Field(None, alias="route_system")
    sig: Optional[str] = None
    startDate: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


# ---------------------------------------------------------------------------
# DetailObservation schema
# ---------------------------------------------------------------------------
class DetailObservation(DetailBase):
    unit: Optional[str] = None
    value: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


# ---------------------------------------------------------------------------
# DetailNote schema
# ---------------------------------------------------------------------------
class DetailNote(DetailBase):
    date: Optional[str] = None
    noteText: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


# ---------------------------------------------------------------------------
# DetailCondition schema
# ---------------------------------------------------------------------------
class DetailCondition(DetailBase):
    pass  # Inherits all fields from DetailBase

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


# ---------------------------------------------------------------------------
# DetailMeasurement schema
# ---------------------------------------------------------------------------
class DetailMeasurement(DetailBase):
    date: Optional[str] = None
    rangeHigh: Optional[int] = None
    rangeLow: Optional[int] = None
    unit: Optional[str] = None
    value: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

# ---------------------------------------------------------------------------
# Content – represents a single observation's payload
# ---------------------------------------------------------------------------
class Content(BaseModel):
    contentId: int = Field(alias="content_id")
    date: Optional[str] = None
    category: Optional[str] = None
    section: Optional[str] = None
    question: Optional[str] = None
    derivedValue: Optional[Value] = None
    details: Optional[List[Union[DetailUserData, DetailMedication, DetailObservation, DetailNote, DetailCondition, DetailMeasurement]]] = None
    sourceValue: Optional[Value] = None
    # Additional fields from the full spec (annotation, flag, etc.)
    # are omitted here for brevity; they can be added later if needed.

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

# ---------------------------------------------------------------------------
# CaseData – the top‑level response model
# ---------------------------------------------------------------------------
class CaseData(BaseModel):
    caseId: int = Field(alias="case_id")
    contents: List[Content]
    count: int

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


# ---------------------------------------------------------------------------
# Cases – represents a list of ModelCase objects
# ---------------------------------------------------------------------------
class Cases(BaseModel):
    case: List[ModelCase] = Field(alias="cases")
    count: int

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )
