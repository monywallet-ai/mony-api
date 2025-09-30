from typing import List, Optional
from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

from app.core.log_utils import log_database_operation
from app.core.logging import database_logger
from app.models.transaction import Transaction, TransactionType
from app.schemas.transaction import TransactionCreate, TransactionResponse


def _process_items_for_jsonb(items: List) -> List:
    """Convert items with Decimal values to JSON-serializable format"""
    if not items:
        return []

    processed_items = []
    for item in items:
        if hasattr(item, "model_dump"):
            item_dict = item.model_dump()
        else:
            item_dict = item

        # Convert Decimal to float for JSON serialization
        for key, value in item_dict.items():
            if hasattr(value, "__class__") and value.__class__.__name__ == "Decimal":
                item_dict[key] = float(value) if value is not None else None

        processed_items.append(item_dict)
    return processed_items


class TransactionCRUD:
    @log_database_operation("create")
    def create(self, db: Session, transaction_data: TransactionCreate) -> Transaction:
        # Convert Pydantic model to dict and handle items serialization
        transaction_dict = transaction_data.model_dump()

        # Process items for JSONB storage
        if transaction_dict.get("items"):
            transaction_dict["items"] = _process_items_for_jsonb(
                transaction_dict["items"]
            )

        db_transaction = Transaction(**transaction_dict)
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        return db_transaction

    @log_database_operation("read")
    def get(self, db: Session, transaction_id: int) -> Optional[Transaction]:
        return db.query(Transaction).filter(Transaction.id == transaction_id).first()

    @log_database_operation("read")
    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        transaction_type: Optional[TransactionType] = None,
        category: Optional[str] = None,
        merchant: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        currency: Optional[str] = None,
        sort_by: str = "date",
        sort_order: str = "desc",
    ) -> List[Transaction]:
        query = db.query(Transaction)

        # Apply filters
        if transaction_type:
            query = query.filter(Transaction.transaction_type == transaction_type)

        if category:
            query = query.filter(Transaction.category == category)

        if merchant:
            query = query.filter(Transaction.merchant.ilike(f"%{merchant}%"))

        if date_from:
            query = query.filter(Transaction.date >= date_from)

        if date_to:
            query = query.filter(Transaction.date <= date_to)

        if currency:
            query = query.filter(Transaction.currency == currency)

        # Apply sorting
        if hasattr(Transaction, sort_by):
            sort_column = getattr(Transaction, sort_by)
            if sort_order.lower() == "asc":
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))
        else:
            # Default sorting by date descending
            query = query.order_by(desc(Transaction.date))

        return query.offset(skip).limit(limit).all()

    @log_database_operation("update")
    def update(
        self, db: Session, transaction_id: int, transaction_update
    ) -> Optional[Transaction]:
        db_transaction = self.get(db, transaction_id)
        if not db_transaction:
            return None

        # Convert update data to dict
        update_data = transaction_update.model_dump(exclude_unset=True)

        # Handle items serialization for JSONB
        if "items" in update_data and update_data["items"] is not None:
            update_data["items"] = _process_items_for_jsonb(update_data["items"])

        # Update fields
        for field, value in update_data.items():
            setattr(db_transaction, field, value)

        db.commit()
        db.refresh(db_transaction)
        return db_transaction

    @log_database_operation("delete")
    def delete(self, db: Session, transaction_id: int) -> bool:
        db_transaction = self.get(db, transaction_id)
        if not db_transaction:
            return False

        db.delete(db_transaction)
        db.commit()
        return True

    @log_database_operation("read")
    def get_total_by_type(
        self, db: Session, transaction_type: TransactionType
    ) -> Decimal:
        result = (
            db.query(Transaction.total_amount)
            .filter(Transaction.transaction_type == transaction_type)
            .all()
        )
        return sum(amount[0] for amount in result) if result else Decimal("0.0")

    @log_database_operation("read")
    def get_monthly_summary(self, db: Session, year: int, month: int) -> dict:
        from sqlalchemy import extract, func

        # Filter transactions for the specific month and year
        transactions = (
            db.query(Transaction)
            .filter(
                and_(
                    extract("year", Transaction.date) == year,
                    extract("month", Transaction.date) == month,
                )
            )
            .all()
        )

        summary = {
            "expenses": Decimal("0.0"),
            "income": Decimal("0.0"),
            "savings": Decimal("0.0"),
            "investments": Decimal("0.0"),
            "total_transactions": len(transactions),
            "categories": {},
        }

        for transaction in transactions:
            amount = transaction.total_amount
            transaction_type = transaction.transaction_type.value

            type_mapping = {
                "expense": "expenses",
                "income": "income",
                "saving": "savings",
                "investment": "investments",
            }

            if transaction_type in type_mapping:
                summary[type_mapping[transaction_type]] += amount

            category = transaction.category or "uncategorized"
            if category not in summary["categories"]:
                summary["categories"][category] = Decimal("0.0")
            summary["categories"][category] += amount

        return summary

    @log_database_operation("read")
    def search(
        self, db: Session, search_term: str, limit: int = 20
    ) -> List[Transaction]:
        return (
            db.query(Transaction)
            .filter(
                or_(
                    Transaction.merchant.ilike(f"%{search_term}%"),
                    Transaction.description.ilike(f"%{search_term}%"),
                    Transaction.category.ilike(f"%{search_term}%"),
                    Transaction.reference_number.ilike(f"%{search_term}%"),
                )
            )
            .limit(limit)
            .all()
        )


transaction_crud = TransactionCRUD()
