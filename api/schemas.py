# core_project/api/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional

class Party(BaseModel):
    name: str
    role: str = Field(..., description="Role in the document: 'Grantor', 'Grantee', 'Lender', 'Trustee', etc.")

class LandRecord(BaseModel):
    document_type: str = Field(..., description="Type of legal instrument, e.g., 'Warranty Deed', 'Deed of Trust'.")
    parties: List[Party]
    property_address: Optional[str] = Field(None, description="Physical address of the property, if mentioned.")
    legal_description: str = Field(..., description="The full, formal legal text describing the boundaries or lot/block.")
    consideration_amount: Optional[float] = Field(None, description="Monetary value exchanged, if listed.")
    execution_date: Optional[str] = Field(None, description="Date the document was signed in YYYY-MM-DD format.")
    county_of_record: Optional[str] = Field(None, description="The county where the deed is recorded.")