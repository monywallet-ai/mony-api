from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from enum import Enum


class TransactionType(str, Enum):
    EXPENSE = "expense"
    INCOME = "income"
    SAVING = "saving"
    INVESTMENT = "investment"


class TransactionItem(BaseModel):
    name: str
    quantity: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    total_price: Optional[Decimal] = None


class TransactionBase(BaseModel):
    transaction_type: TransactionType = TransactionType.EXPENSE
    merchant: str
    date: date
    total_amount: Decimal
    currency: str = "USD"
    payment_method: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    reference_number: Optional[str] = None
    taxes: Optional[Decimal] = None
    items: List[TransactionItem] = []


class TransactionCreate(TransactionBase):
    pass


class TransactionResponse(TransactionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime