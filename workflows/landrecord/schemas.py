from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class LandRecordExtraction(BaseModel):
    book: Optional[str] = Field(None, description="Book number where the document is recorded.")
    page: Optional[str] = Field(None, description="Page number within the book.")
    page_range: Optional[str] = Field(None, description="Number of pages in the document.")
    state: Optional[str] = Field(None, description="State where the property is located.")
    county: Optional[str] = Field(None, description="County where the property is located.")
    individual_parties: list[IndividualPartyExtraction] = Field(default_factory=list)
    firm_parties: list[FirmPartyExtraction] = Field(default_factory=list)
    references: list[ReferenceExtraction] = Field(default_factory=list)
    document_type: Optional[str] = Field(None, description="Type of land record: DEED, MORTGAGE, RELEASE, LIEN, ASSIGNMENT, other.")
    execution_date: Optional[str] = Field(None, description="Date the document was executed, in YYYY-MM-DD format.")
    recorded_date: Optional[str] = Field(None, description="Date the document was recorded, in YYYY-MM-DD format.")
    property_address: Optional[str] = Field(None, description="Street address of the property.")
    brief_legal_description: Optional[str] = Field(None, description="Brief legal description or document title.")
    legal_description: Optional[str] = Field(None, description="Full legal description of the property.")
    consideration_amount: Optional[str] = Field(None, description="Monetary consideration amount stated in the document.")


class IndividualPartyExtraction(BaseModel):
    name: Optional[str] = Field(None, description="Full name of the individual.")
    party_type: Optional[str] = Field(None, description="Role of the party: GRANTOR or GRANTEE.")
    givenname: Optional[str] = Field(None, description="Given name of the individual.")
    surname: Optional[str] = Field(None, description="Surname of the individual.")
    designated_status: Optional[str] = Field(None, description="Designated status (e.g. trustee, executor), if any.")


class FirmPartyExtraction(BaseModel):
    name: Optional[str] = Field(None, description="Full name of the firm or entity.")
    party_type: Optional[str] = Field(None, description="Role of the party: GRANTOR or GRANTEE.")
    designated_status: Optional[str] = Field(None, description="Designated status (e.g. trustee, lender), if any.")


class ReferenceExtraction(BaseModel):
    book: Optional[str] = None
    page: Optional[str] = None
    document_type: Optional[str] = None
