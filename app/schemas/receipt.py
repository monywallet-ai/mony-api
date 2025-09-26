from datetime import date as Date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ReceiptItem(BaseModel):
    name: str = Field(..., description="Item name or description", example="Rice 5kg")
    quantity: Optional[Decimal] = Field(None, description="Quantity of the item", example=1.0)
    unit_price: Optional[Decimal] = Field(None, description="Price per unit", example=25000.0)
    total_price: Optional[Decimal] = Field(None, description="Total price for this item", example=25000.0)

    model_config = ConfigDict(
        json_encoders={
            Decimal: float
        },
        json_schema_extra={
            "example": {
                "name": "Rice 5kg",
                "quantity": 1.0,
                "unit_price": 25000.0,
                "total_price": 25000.0
            }
        }
    )


class ReceiptData(BaseModel):
    merchant: str = Field(..., description="Name of the store, company, or issuing entity", example="La Esperanza Supermarket")
    date: Date = Field(..., description="Issue date in YYYY-MM-DD format", example="2025-09-20")
    total_amount: Decimal = Field(..., description="Total amount paid", example=152000.0)
    currency: str = Field(..., description="Currency in ISO format (e.g., USD, COP, EUR)", example="COP")
    payment_method: Optional[str] = Field(None, description="Payment method used", example="debit card")
    category: Optional[str] = Field(None, description="Expense category", example="groceries")
    description: Optional[str] = Field(None, description="Brief summary of the receipt", example="Purchase of groceries and household products")
    receipt_number: Optional[str] = Field(None, description="Receipt or invoice number", example="FAC-908123")
    taxes: Optional[Decimal] = Field(None, description="Total tax or VAT amount", example=19000.0)
    items: List[ReceiptItem] = Field(default=[], description="List of purchased products or services")

    model_config = ConfigDict(
        json_encoders={
            Decimal: float
        },
        json_schema_extra={
            "example": {
                "merchant": "La Esperanza Supermarket",
                "date": "2025-09-20",
                "total_amount": 152000.0,
                "currency": "COP",
                "payment_method": "debit card",
                "category": "groceries",
                "description": "Purchase of groceries and household products",
                "receipt_number": "FAC-908123",
                "taxes": 19000.0,
                "items": [
                    {
                        "name": "Rice 5kg",
                        "quantity": 1,
                        "unit_price": 25000.0,
                        "total_price": 25000.0
                    },
                    {
                        "name": "Oil 1L",
                        "quantity": 2,
                        "unit_price": 15000.0,
                        "total_price": 30000.0
                    }
                ]
            }
        }
    )


class ReceiptAnalysisResponse(BaseModel):
    receipt: ReceiptData = Field(..., description="Extracted receipt data from the uploaded image")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "receipt": {
                    "merchant": "La Esperanza Supermarket",
                    "date": "2025-09-20",
                    "total_amount": 152000.0,
                    "currency": "COP",
                    "payment_method": "debit card",
                    "category": "groceries",
                    "description": "Purchase of groceries and household products",
                    "receipt_number": "FAC-908123",
                    "taxes": 19000.0,
                    "items": [
                        {
                            "name": "Rice 5kg",
                            "quantity": 1,
                            "unit_price": 25000.0,
                            "total_price": 25000.0
                        }
                    ]
                }
            }
        }
    )


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message", example="Invalid file type")
    error_code: Optional[str] = Field(None, description="Error code for programmatic handling", example="INVALID_FILE_TYPE")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "Invalid file type",
                "error_code": "INVALID_FILE_TYPE"
            }
        }
    )