# core_project/api/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class Party(BaseModel):
    name: str
    role: Literal['Grantor', 'Grantee']  = Field(..., description="Role of the people involved in the document: 'Grantor' the seller or 'Grantee' the buyer")

class Reference(BaseModel):
    book: Optional[str] = Field(..., description="sometimes, documents have other documents referenced, The reference volume, often prefixed by 'Book', 'B', 'BK' which may be alphanumeric or hexadecimal. return the exact value.")
    page: Optional[str] = Field(..., description="sometimes, documents have other documents referenced, The reference page number, often prefixed by 'Page', 'Pg', or 'P', which may be alphanumeric or hexadecimal. return the exact value.")
    document_type: Optional[str] = Field(..., description="Type of legal instrument, land record, return the exact value.")

class LandRecord(BaseModel):
    document_type: str = Field(..., description="Type of legal instrument, land record")
    book: Optional[str] = Field(..., pattern=r'^[A-Z][0-9]{1,5}$', description="The record volume, often prefixed by 'Book' or 'Vol'. The value MUST be an alphanumeric code between A1 and Z999. Extract the value only, without the prefix.")
    page: Optional[str] = Field(..., description="The record page number, often prefixed by 'Page', 'Pg', or 'P', which may be alphanumeric or hexadecimal")
    parties: List[Party]
    references: Optional[List[Reference]]
    property_address: Optional[str] = Field(..., description="Physical address of the property in the document.")
    legal_description: str = Field(..., description="The full, formal legal text describing the boundaries or lot/block.")
    consideration_amount: Optional[float] = Field(None, description="Monetary value exchanged, if listed.")
    execution_date: Optional[str] = Field(..., description="Date the document was signed or presented in MM-DD-YYYY format.")
    county_of_record: Optional[str] = Field(None, description="The county where the land record document is recorded.")