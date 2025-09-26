from datetime import date
from decimal import Decimal
from sqlalchemy import Column, String, Date, Numeric, Text, Enum
from sqlalchemy.dialects.postgresql import JSONB
import enum

from .base import BaseModel


class TransactionType(enum.Enum):
    EXPENSE = "expense"
    INCOME = "income"
    SAVING = "saving"
    INVESTMENT = "investment"


class Transaction(BaseModel):
    __tablename__ = "transactions"

    transaction_type = Column(Enum(TransactionType), nullable=False, default=TransactionType.EXPENSE)
    merchant = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    payment_method = Column(String(50), nullable=True)
    category = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    reference_number = Column(String(100), nullable=True)
    taxes = Column(Numeric(15, 2), nullable=True)
    items = Column(JSONB, nullable=True, default=[])