from datetime import date as Date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from enum import Enum

from .error import (
    ValidationErrorResponse,
    NotFoundErrorResponse,
    RateLimitErrorResponse,
    InternalServerErrorResponse
)


class TransactionType(str, Enum):
    expense = "expense"
    income = "income"
    saving = "saving"
    investment = "investment"


class TransactionItem(BaseModel):
    name: str = Field(..., description="Name or description of the item", example="Coffee")
    quantity: Optional[Decimal] = Field(None, description="Quantity of the item", example=2.0)
    unit_price: Optional[Decimal] = Field(None, description="Price per unit", example=4.50)
    total_price: Optional[Decimal] = Field(None, description="Total price for this item", example=9.00)

    model_config = ConfigDict(
        json_encoders={
            Decimal: float
        },
        json_schema_extra={
            "example": {
                "name": "Coffee",
                "quantity": 2.0,
                "unit_price": 4.50,
                "total_price": 9.00
            }
        }
    )


class TransactionBase(BaseModel):
    transaction_type: TransactionType = Field(
        default=TransactionType.expense,
        description="Type of transaction",
        example=TransactionType.expense
    )
    merchant: str = Field(..., description="Name of the merchant or entity", example="Starbucks")
    date: Date = Field(..., description="Transaction date", example="2024-03-15")
    total_amount: Decimal = Field(..., description="Total amount of the transaction", example=25.50)
    currency: str = Field(default="USD", description="Currency code (ISO 4217)", example="USD")
    payment_method: Optional[str] = Field(None, description="Payment method used", example="credit card")
    category: Optional[str] = Field(None, description="Transaction category", example="dining")
    description: Optional[str] = Field(None, description="Additional description", example="Morning coffee and snacks")
    reference_number: Optional[str] = Field(None, description="Reference or receipt number", example="REC-001234")
    taxes: Optional[Decimal] = Field(None, description="Tax amount", example=2.50)
    items: List[TransactionItem] = Field(default=[], description="List of items in the transaction")

    model_config = ConfigDict(
        json_encoders={
            Decimal: float
        }
    )


class TransactionCreate(TransactionBase):
    model_config = ConfigDict(
        json_encoders={
            Decimal: float
        },
        json_schema_extra={
            "example": {
                "transaction_type": "expense",
                "merchant": "Starbucks",
                "date": "2024-03-15",
                "total_amount": 25.50,
                "currency": "USD",
                "payment_method": "credit card",
                "category": "dining",
                "description": "Morning coffee and snacks",
                "reference_number": "REC-001234",
                "taxes": 2.50,
                "items": [
                    {
                        "name": "Latte",
                        "quantity": 2,
                        "unit_price": 5.50,
                        "total_price": 11.00
                    },
                    {
                        "name": "Croissant",
                        "quantity": 1,
                        "unit_price": 3.50,
                        "total_price": 3.50
                    }
                ]
            }
        }
    )


class TransactionUpdate(BaseModel):
    transaction_type: Optional[TransactionType] = None
    merchant: Optional[str] = None
    date: Optional[Date] = None
    total_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    payment_method: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    reference_number: Optional[str] = None
    taxes: Optional[Decimal] = None
    items: Optional[List[TransactionItem]] = None

    model_config = ConfigDict(
        json_encoders={
            Decimal: float
        },
        json_schema_extra={
            "example": {
                "category": "groceries",
                "description": "Updated description"
            }
        }
    )


class TransactionResponse(TransactionBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            Decimal: float
        }
    )

    id: int = Field(..., description="Unique transaction ID", example=1)
    created_at: datetime = Field(..., description="Transaction creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]
    total: int = Field(..., description="Total number of transactions", example=150)
    skip: int = Field(..., description="Number of skipped transactions", example=0)
    limit: int = Field(..., description="Number of transactions per page", example=20)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "transactions": [],
                "total": 150,
                "skip": 0,
                "limit": 20
            }
        }
    )


class TransactionSummary(BaseModel):
    expenses: Decimal = Field(..., description="Total expenses", example=1250.50)
    income: Decimal = Field(..., description="Total income", example=3500.00)
    savings: Decimal = Field(..., description="Total savings", example=500.00)
    investments: Decimal = Field(..., description="Total investments", example=750.00)
    total_transactions: int = Field(..., description="Total number of transactions", example=45)
    categories: Dict[str, Decimal] = Field(..., description="Breakdown by category")

    model_config = ConfigDict(
        json_encoders={
            Decimal: float
        },
        json_schema_extra={
            "example": {
                "expenses": 1250.50,
                "income": 3500.00,
                "savings": 500.00,
                "investments": 750.00,
                "total_transactions": 45,
                "categories": {
                    "dining": 350.75,
                    "groceries": 480.25,
                    "transportation": 125.50,
                    "entertainment": 294.00
                }
            }
        }
    )


class TransactionFilters(BaseModel):
    transaction_type: Optional[TransactionType] = Field(None, description="Filter by transaction type")
    category: Optional[str] = Field(None, description="Filter by category")
    merchant: Optional[str] = Field(None, description="Filter by merchant name")
    date_from: Optional[Date] = Field(None, description="Start date filter")
    date_to: Optional[Date] = Field(None, description="End date filter")
    currency: Optional[str] = Field(None, description="Filter by currency")
    skip: int = Field(0, ge=0, description="Number of transactions to skip")
    limit: int = Field(20, ge=1, le=100, description="Number of transactions to return")
    sort_by: str = Field("date", description="Field to sort by")
    sort_order: str = Field("desc", description="Sort order (asc or desc)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "transaction_type": "expense",
                "category": "dining",
                "date_from": "2024-01-01",
                "date_to": "2024-03-31",
                "skip": 0,
                "limit": 20,
                "sort_by": "date",
                "sort_order": "desc"
            }
        }
    )


# Swagger Response Documentation
transaction_responses = {
    "create_transaction": {
        422: {
            "model": ValidationErrorResponse,
            "description": "Validation error",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_amount": {
                            "summary": "Invalid transaction amount",
                            "value": {
                                "success": False,
                                "error_code": "VALIDATION_ERROR",
                                "message": "Transaction amount must be greater than 0",
                                "details": {
                                    "field": "total_amount",
                                    "value": -50.0
                                },
                                "timestamp": "2024-10-01T12:00:00Z",
                                "request_id": "req_abc123"
                            }
                        },
                        "empty_merchant": {
                            "summary": "Empty merchant name",
                            "value": {
                                "success": False,
                                "error_code": "VALIDATION_ERROR",
                                "message": "Merchant name is required",
                                "details": {
                                    "field": "merchant",
                                    "value": ""
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
                        "message": "Too many requests. Limit: 50 per 60 seconds",
                        "limit": 50,
                        "window": "60 seconds",
                        "retry_after": 45,
                        "timestamp": "2024-10-01T12:00:00Z",
                        "request_id": "req_abc123"
                    }
                }
            }
        },
        500: {
            "model": InternalServerErrorResponse,
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error_code": "DATABASE_ERROR",
                        "message": "Failed to create transaction",
                        "details": {
                            "operation": "create"
                        },
                        "timestamp": "2024-10-01T12:00:00Z",
                        "request_id": "req_abc123"
                    }
                }
            }
        }
    },

    "get_transactions": {
        429: {
            "model": RateLimitErrorResponse,
            "description": "Rate limit exceeded"
        },
        500: {
            "model": InternalServerErrorResponse,
            "description": "Internal server error"
        }
    },

    "get_transaction": {
        404: {
            "model": NotFoundErrorResponse,
            "description": "Transaction not found",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error_code": "RESOURCE_NOT_FOUND",
                        "message": "Transaction with ID 999 not found",
                        "details": {
                            "resource": "Transaction",
                            "resource_id": "999"
                        },
                        "timestamp": "2024-10-01T12:00:00Z",
                        "request_id": "req_abc123"
                    }
                }
            }
        },
        429: {
            "model": RateLimitErrorResponse,
            "description": "Rate limit exceeded"
        },
        500: {
            "model": InternalServerErrorResponse,
            "description": "Internal server error"
        }
    },

    "update_transaction": {
        404: {
            "model": NotFoundErrorResponse,
            "description": "Transaction not found"
        },
        422: {
            "model": ValidationErrorResponse,
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error_code": "VALIDATION_ERROR",
                        "message": "Transaction amount must be greater than 0",
                        "details": {
                            "field": "total_amount",
                            "value": -25.0
                        },
                        "timestamp": "2024-10-01T12:00:00Z",
                        "request_id": "req_abc123"
                    }
                }
            }
        },
        429: {
            "model": RateLimitErrorResponse,
            "description": "Rate limit exceeded"
        },
        500: {
            "model": InternalServerErrorResponse,
            "description": "Internal server error"
        }
    },

    "delete_transaction": {
        404: {
            "model": NotFoundErrorResponse,
            "description": "Transaction not found"
        },
        429: {
            "model": RateLimitErrorResponse,
            "description": "Rate limit exceeded"
        },
        500: {
            "model": InternalServerErrorResponse,
            "description": "Internal server error"
        }
    },

    "get_monthly_summary": {
        422: {
            "model": ValidationErrorResponse,
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error_code": "VALIDATION_ERROR",
                        "message": "Month must be between 1 and 12",
                        "details": {
                            "field": "month",
                            "value": 13
                        },
                        "timestamp": "2024-10-01T12:00:00Z",
                        "request_id": "req_abc123"
                    }
                }
            }
        },
        429: {
            "model": RateLimitErrorResponse,
            "description": "Rate limit exceeded"
        },
        500: {
            "model": InternalServerErrorResponse,
            "description": "Internal server error"
        }
    },

    "search_transactions": {
        422: {
            "model": ValidationErrorResponse,
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error_code": "VALIDATION_ERROR",
                        "message": "Search term must be at least 2 characters long",
                        "details": {
                            "field": "search_term",
                            "value": "a"
                        },
                        "timestamp": "2024-10-01T12:00:00Z",
                        "request_id": "req_abc123"
                    }
                }
            }
        },
        429: {
            "model": RateLimitErrorResponse,
            "description": "Rate limit exceeded"
        },
        500: {
            "model": InternalServerErrorResponse,
            "description": "Internal server error"
        }
    },

    "get_totals_by_type": {
        429: {
            "model": RateLimitErrorResponse,
            "description": "Rate limit exceeded"
        },
        500: {
            "model": InternalServerErrorResponse,
            "description": "Internal server error"
        }
    }
}