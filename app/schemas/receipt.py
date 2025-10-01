from datetime import date as Date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from .error import FileProcessingErrorResponse, RateLimitErrorResponse


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


# Swagger Response Documentation
receipt_responses = {
    "analyze_receipt": {
        400: {
            "model": FileProcessingErrorResponse,
            "description": "File processing error",
            "content": {
                "application/json": {
                    "examples": {
                        "missing_file": {
                            "summary": "No file provided",
                            "value": {
                                "success": False,
                                "error_code": "FILE_PROCESSING_ERROR",
                                "message": "No file provided",
                                "filename": None,
                                "error_type": "MISSING_FILE",
                                "timestamp": "2024-10-01T12:00:00Z",
                                "request_id": "req_abc123"
                            }
                        },
                        "unsupported_format": {
                            "summary": "Unsupported file format",
                            "value": {
                                "success": False,
                                "error_code": "FILE_PROCESSING_ERROR",
                                "message": "Invalid file type. Allowed types: image/png, image/jpeg, image/jpg",
                                "filename": "document.pdf",
                                "file_type": "application/pdf",
                                "error_type": "UNSUPPORTED_FORMAT",
                                "details": {
                                    "supported_formats": ["image/png", "image/jpeg", "image/jpg"]
                                },
                                "timestamp": "2024-10-01T12:00:00Z",
                                "request_id": "req_abc123"
                            }
                        },
                        "file_too_large": {
                            "summary": "File size exceeds limit",
                            "value": {
                                "success": False,
                                "error_code": "FILE_PROCESSING_ERROR",
                                "message": "File too large. Maximum size allowed: 10MB",
                                "filename": "large_receipt.jpg",
                                "file_type": "image/jpeg",
                                "error_type": "FILE_TOO_LARGE",
                                "details": {
                                    "file_size": 15728640,
                                    "max_size": 10485760,
                                    "max_size_mb": 10
                                },
                                "timestamp": "2024-10-01T12:00:00Z",
                                "request_id": "req_abc123"
                            }
                        }
                    }
                }
            }
        },
        422: {
            "model": FileProcessingErrorResponse,
            "description": "Receipt processing error",
            "content": {
                "application/json": {
                    "examples": {
                        "extraction_failed": {
                            "summary": "Could not extract receipt data",
                            "value": {
                                "success": False,
                                "error_code": "FILE_PROCESSING_ERROR",
                                "message": "Could not extract receipt data from the provided image",
                                "filename": "blurry_receipt.jpg",
                                "file_type": "image/jpeg",
                                "error_type": "EXTRACTION_FAILED",
                                "details": {
                                    "reason": "Empty AI response"
                                },
                                "timestamp": "2024-10-01T12:00:00Z",
                                "request_id": "req_abc123"
                            }
                        },
                        "ai_processing_failed": {
                            "summary": "AI analysis failed",
                            "value": {
                                "success": False,
                                "error_code": "FILE_PROCESSING_ERROR",
                                "message": "AI analysis failed: Service temporarily unavailable",
                                "filename": "receipt.png",
                                "file_type": "image/png",
                                "error_type": "AI_PROCESSING_FAILED",
                                "details": {
                                    "original_error": "Service temporarily unavailable"
                                },
                                "timestamp": "2024-10-01T12:00:00Z",
                                "request_id": "req_abc123"
                            }
                        },
                        "response_parsing_failed": {
                            "summary": "Failed to parse AI response",
                            "value": {
                                "success": False,
                                "error_code": "FILE_PROCESSING_ERROR",
                                "message": "Failed to parse AI response: Invalid JSON format",
                                "filename": "receipt.jpg",
                                "file_type": "image/jpeg",
                                "error_type": "RESPONSE_PARSING_FAILED",
                                "details": {
                                    "parse_error": "Expecting value: line 1 column 1 (char 0)",
                                    "ai_response": "The receipt shows a purchase at..."
                                },
                                "timestamp": "2024-10-01T12:00:00Z",
                                "request_id": "req_abc123"
                            }
                        }
                    }
                }
            }
        },
        429: {
            "model": RateLimitErrorResponse,
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Limit: 10 per 60 seconds",
                        "limit": 10,
                        "window": "60 seconds",
                        "retry_after": 60,
                        "timestamp": "2024-10-01T12:00:00Z",
                        "request_id": "req_abc123"
                    }
                }
            }
        }
    }
}