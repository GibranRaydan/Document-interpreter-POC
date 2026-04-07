from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class PartyExtraction(BaseModel):
    name: Optional[str] = Field(None, description="Surname or full entity name.")
    givenname: Optional[str] = Field(None, description="Given name for individuals.")
    role: Optional[Literal["GRANTOR", "GRANTEE", "TRUSTEE", "LENDER"]] = Field(
        None, description="Role of the party in the document."
    )
    type: Optional[Literal["F", "I"]] = Field(
        None, description="'I' for individual, 'F' for firm/entity."
    )


class ReferenceExtraction(BaseModel):
    book: Optional[str] = None
    page: Optional[str] = None
    document_type: Optional[str] = None


class LandRecordExtraction(BaseModel):
    book: Optional[str] = Field(None, description="Book number where the document is recorded.")
    page: Optional[str] = Field(None, description="Page number within the book.")
    document_type: Optional[str] = Field(
        None, description="Type of land record: deeds, mortgages, releases, liens, assignments, other."
    )
    page_range: Optional[str] = Field(None, description="Page range of the document (e.g. '12-15').")
    property_address: Optional[str] = Field(None, description="Street address of the property.")
    legal_description: Optional[str] = Field(
        None, description="Full legal description of the property."
    )
    consideration_amount: Optional[str] = Field(
        None, description="Monetary consideration amount stated in the document."
    )
    execution_date: Optional[str] = Field(
        None, description="Date the document was executed, in YYYY-MM-DD format."
    )
    county: Optional[str] = Field(None, description="County where the property is located.")
    state: Optional[str] = Field(None, description="State where the property is located.")
    parties: list[PartyExtraction] = Field(
        default_factory=list,
        description="List of grantors and grantees involved in the document.",
    )
    references: list[ReferenceExtraction] = Field(
        default_factory=list,
        description="References to other recorded documents cited in this document.",
    )
