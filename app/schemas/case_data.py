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
# Detail schemas – we only need DetailUserData for this endpoint.
# The OpenAPI spec defines a DetailBase with a tableDisplayText field; we
# replicate the fields that are populated from fact_relationship.
# ---------------------------------------------------------------------------
class DetailBase(BaseModel):
    domainConceptId1: Optional[int] = Field(alias="domain_concept_id_1", default=None)
    factId1: Optional[int] = Field(alias="fact_id_1", default=None)
    domainConceptId2: Optional[int] = Field(alias="domain_concept_id_2", default=None)
    factId2: Optional[int] = Field(alias="fact_id_2", default=None)
    relationshipConceptId: Optional[int] = Field(alias="relationship_concept_id", default=None)
    tableDisplayText: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=lambda s: s,
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
