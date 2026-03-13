from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field
from typing import Literal


# --- Shared nested models ---

class Party(BaseModel):
    name: str = Field(..., description="Full name of person or entity.")
    role: Literal["buyer", "seller", "vendor", "client", "other"] = Field(
        ..., description="Role of the party in the transaction."
    )
    type: Literal["I", "F"] = Field(
        ..., description="'I' for individual, 'F' for firm/entity."
    )


class LineItem(BaseModel):
    description: str = Field(..., description="Product or service description.")
    quantity: Optional[float] = Field(None, description="Number of units.")
    unit_price: Optional[float] = Field(
        None, description="Price per unit in the document currency."
    )
    total: Optional[float] = Field(
        None, description="quantity × unit_price for this line."
    )


# --- Invoice Schema ---

class InvoiceSchema(BaseModel):
    vendor_name: str = Field(
        ..., description="Full legal name of the vendor issuing the invoice."
    )
    invoice_number: str = Field(
        ..., description="Unique invoice ID as printed on the document."
    )
    issue_date: Optional[str] = Field(
        None, description="Invoice issue date in YYYY-MM-DD format."
    )
    due_date: Optional[str] = Field(
        None, description="Payment due date in YYYY-MM-DD format."
    )
    currency: str = Field(
        default="USD",
        description="ISO 4217 currency code (e.g. USD, MXN, EUR).",
    )
    subtotal: Optional[float] = Field(None, description="Amount before taxes.")
    tax: Optional[float] = Field(None, description="Total tax amount.")
    total_amount: float = Field(
        ..., description="Grand total due, including taxes."
    )
    payment_terms: Optional[str] = Field(
        None, description="E.g. 'Net 30', 'Due on receipt'."
    )
    parties: List[Party] = Field(default_factory=list)
    line_items: List[LineItem] = Field(default_factory=list)


# --- Receipt Schema ---

class ReceiptItem(BaseModel):
    description: str = Field(..., description="Item description.")
    quantity: Optional[float] = Field(None, description="Quantity purchased.")
    price: Optional[float] = Field(None, description="Total price for this item.")


class ReceiptSchema(BaseModel):
    store_name: str = Field(..., description="Name of the store or merchant.")
    issue_date: Optional[str] = Field(
        None, description="Transaction date in YYYY-MM-DD format."
    )
    subtotal: Optional[float] = Field(None, description="Amount before taxes.")
    tax: Optional[float] = Field(None, description="Tax amount.")
    total: float = Field(..., description="Total amount paid.")
    payment_method: Optional[str] = Field(
        None, description="Cash, Visa, Mastercard, etc."
    )
    last_four: Optional[str] = Field(
        None, description="Last 4 digits of card, if applicable."
    )
    items: List[ReceiptItem] = Field(default_factory=list)


# --- Schema Map ---

SCHEMAS_MAP: dict[str, type[BaseModel]] = {
    "invoice": InvoiceSchema,
    "receipt": ReceiptSchema,
}
