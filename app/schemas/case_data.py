from __future__ import annotations

from typing import List, Optional

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
# Content – represents a single observation's payload
# ---------------------------------------------------------------------------
class Content(BaseModel):
    contentId: int = Field(alias="content_id")
    date: Optional[str] = None
    category: Optional[str] = None
    section: Optional[str] = None
    question: Optional[str] = None
    derivedValue: Optional[Value] = None
    details: Optional[List[DetailUserData]] = None
    # Additional fields from the full spec (annotation, flag, sourceValue, etc.)
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
