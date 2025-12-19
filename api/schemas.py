# core_project/api/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class Party(BaseModel):

    name: str = Field(..., description="name of the people and entities involved in the document,"
                                        "if its a entity like a company this will be the complete name,"
                                        "if its a person, this is the first name of that person." \
                                        "return just the exact value of the name")
    givenname: Optional[str] = Field(None,
                                     description="If it is the surname/givenname of a person " \
                                     "If 'type' is 'I' (Individual), return the person's **Given Name(s)/First Name** (e.g., ." \
                                     "If 'type' is 'F' (Entity/Company), this field **MUST be None**." \
                                     "return just the exact value of the name")
    
    role: Literal['Grantor', 'Grantee']  = Field(..., description="Role of the people involved in the document: 'Grantor' the seller or 'Grantee' the buyer")
    type: Literal['F', 'I'] = Field(..., description="If this party is a person or individual, it must return 'I'; if it is an entity and/or company, it must return F'.")

class Reference(BaseModel):
    book: Optional[str] = Field(..., pattern=r'^[A-Z][0-9]{1,5}$',
                                     description="sometimes, documents have other documents referenced," \
                                     " The reference volume, often prefixed by 'Book', 'B', 'BK'" \
                                     " which may be alphanumeric or hexadecimal." \
                                     " this document cannot have the same value 'book' of the main document" \
                                     " return the exact value.")
    page: Optional[str] = Field(..., description="sometimes, documents have other documents referenced, The reference page number," \
                                    " often prefixed by 'Page', 'Pg', or 'P'," \
                                    " which may be alphanumeric or hexadecimal. return the exact value."\
                                    " this document cannot have the same value 'page' of the main document")
    
    document_type: Optional[str] = Field(..., description="Type of legal instrument, land record, return the exact value.")

class LandRecord(BaseModel):
    document_type: str = Field(..., description="Type of legal instrument")
    book: Optional[str] = Field(..., pattern=r'^[A-Z][0-9]{1,5}$', 
                                     description="The record volume, often prefixed by 'Book' or 'Vol'. " \
                                     "The value MUST be an alphanumeric code between A1 and Z999. Extract the value only, without the prefix.")
    page: Optional[int] = Field(..., description="The **STARTING** record page number. If the document shows a range like '100-115' or '100 to 115', you **MUST ONLY** extract the first number ('100'). **DO NOT** include the hyphen, the 'to', or the ending page number. Return the exact starting page number string.")
    page_range: Optional[str] = Field(..., description="The record page range number, often prefixed by 'Page', 'Pg', or 'P', which may be alphanumeric or hexadecimal, return value similar writen as 'initialpage - lastpage'")
    parties: List[Party]
    references: Optional[List[Reference]]
    property_address: Optional[str] = Field(..., description="Physical address of the property in the document.")
    legal_description: str = Field(..., description="The full, formal legal text describing the boundaries or lot/block.")
    consideration_amount: Optional[float] = Field(None, description="Monetary value exchanged, if listed.")
    execution_date: Optional[str] = Field(..., description="Date the document was signed or presented in MM-DD-YYYY format.")
    county: Optional[str] = Field(None, description="The county where the  document is recorded.")
    state: Optional[str] = Field(None, description="The state where the document is recorded.")

