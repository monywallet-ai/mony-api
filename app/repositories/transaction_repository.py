from typing import List, Optional, Dict, Any
from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, and_, or_, extract

from app.repositories.base import BaseRepository
from app.models.transaction import Transaction, TransactionType as ModelTransactionType
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.core.logging import database_logger
from app.core.log_utils import log_database_operation


class TransactionRepository(
    BaseRepository[Transaction, TransactionCreate, TransactionUpdate]
):
    """
    Repository for Transaction entities.

    Provides specialized data access methods for transactions including
    filtering, searching, and aggregation operations.
    """

    def __init__(self, db: Session):
        """Initialize the transaction repository."""
        super().__init__(db, Transaction)

    @log_database_operation("read")
    def get_by_id_with_items(self, transaction_id: int) -> Optional[Transaction]:
        """
        Get transaction by ID with eagerly loaded items.

        Args:
            transaction_id: Transaction ID

        Returns:
            Transaction with items loaded or None if not found
        """
        try:
            stmt = (
                select(Transaction)
                .where(Transaction.id == transaction_id)
            )

            result = self.db.execute(stmt)
            transaction = result.scalar_one_or_none()

            return transaction

        except Exception as e:
            database_logger.error(
                "transaction_with_items_retrieval_failed",
                transaction_id=transaction_id,
                error=str(e),
            )
            raise

    @log_database_operation("read")
    def get_filtered_transactions(
        self,
        skip: int = 0,
        limit: int = 100,
        transaction_type: Optional[ModelTransactionType] = None,
        category: Optional[str] = None,
        merchant: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        currency: Optional[str] = None,
        sort_by: str = "date",
        sort_order: str = "desc",
    ) -> List[Transaction]:
        """
        Get transactions with advanced filtering and sorting.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            transaction_type: Filter by transaction type
            category: Filter by category
            merchant: Filter by merchant name
            date_from: Start date filter
            date_to: End date filter
            currency: Filter by currency
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)

        Returns:
            List of filtered transactions
        """
        try:
            stmt = select(Transaction)

            # Apply filters
            conditions = []

            if transaction_type:
                conditions.append(Transaction.transaction_type == transaction_type)

            if category:
                conditions.append(Transaction.category.ilike(f"%{category}%"))

            if merchant:
                conditions.append(Transaction.merchant.ilike(f"%{merchant}%"))

            if date_from:
                conditions.append(Transaction.date >= date_from)

            if date_to:
                conditions.append(Transaction.date <= date_to)

            if currency:
                conditions.append(Transaction.currency == currency)

            if conditions:
                stmt = stmt.where(and_(*conditions))

            # Apply sorting
            valid_sort_fields = ["date", "total_amount", "merchant", "created_at", "updated_at"]
            if sort_by not in valid_sort_fields:
                sort_by = "date"

            sort_column = getattr(Transaction, sort_by)
            if sort_order.lower() == "desc":
                stmt = stmt.order_by(sort_column.desc())
            else:
                stmt = stmt.order_by(sort_column.asc())

            # Apply pagination
            stmt = stmt.offset(skip).limit(limit)

            result = self.db.execute(stmt)
            transactions = result.scalars().all()

            return transactions

        except Exception as e:
            database_logger.error(
                "filtered_transactions_retrieval_failed", error=str(e)
            )
            raise

    @log_database_operation("read")
    def search_transactions(
        self, search_term: str, limit: int = 20
    ) -> List[Transaction]:
        """
        Search transactions by text across multiple fields.

        Args:
            search_term: Text to search for
            limit: Maximum number of results

        Returns:
            List of matching transactions
        """
        try:
            search_pattern = f"%{search_term}%"

            stmt = (
                select(Transaction)
                .where(
                    or_(
                        Transaction.merchant.ilike(search_pattern),
                        Transaction.description.ilike(search_pattern),
                        Transaction.category.ilike(search_pattern),
                        Transaction.reference_number.ilike(search_pattern),
                    )
                )
                .order_by(Transaction.date.desc())
                .limit(limit)
            )

            result = self.db.execute(stmt)
            transactions = result.scalars().all()

            return transactions

        except Exception as e:
            database_logger.error(
                "transaction_search_failed", search_term=search_term, error=str(e)
            )
            raise

    @log_database_operation("read")
    def get_monthly_summary(self, year: int, month: int) -> Dict[str, Any]:
        """
        Get monthly transaction summary with aggregated data.

        Args:
            year: Year to filter by
            month: Month to filter by

        Returns:
            Dictionary with summary statistics
        """
        try:
            # Get total count
            count_stmt = select(func.count(Transaction.id)).where(
                and_(
                    extract("year", Transaction.date) == year,
                    extract("month", Transaction.date) == month,
                )
            )

            # Get totals by transaction type
            totals_by_type = {}
            for transaction_type in ModelTransactionType:
                total_stmt = select(func.sum(Transaction.total_amount)).where(
                    and_(
                        extract("year", Transaction.date) == year,
                        extract("month", Transaction.date) == month,
                        Transaction.transaction_type == transaction_type,
                    )
                )
                result = self.db.execute(total_stmt)
                total = result.scalar() or Decimal("0")
                totals_by_type[transaction_type.value] = float(total)

            # Get category breakdown
            category_stmt = (
                select(
                    Transaction.category,
                    func.sum(Transaction.total_amount).label("total"),
                    func.count(Transaction.id).label("count"),
                )
                .where(
                    and_(
                        extract("year", Transaction.date) == year,
                        extract("month", Transaction.date) == month,
                        Transaction.category.isnot(None),
                    )
                )
                .group_by(Transaction.category)
            )

            # Execute queries
            total_count = self.db.execute(count_stmt).scalar()
            category_result = self.db.execute(category_stmt)
            category_breakdown = [
                {
                    "category": row.category,
                    "total": float(row.total),
                    "count": row.count,
                }
                for row in category_result
            ]

            summary = {
                "year": year,
                "month": month,
                "total_transactions": total_count,
                "totals_by_type": totals_by_type,
                "category_breakdown": category_breakdown,
            }

            return summary

        except Exception as e:
            database_logger.error(
                "monthly_summary_failed", year=year, month=month, error=str(e)
            )
            raise

    @log_database_operation("read")
    def get_total_by_type(self, transaction_type: ModelTransactionType) -> Decimal:
        """
        Get total amount for a specific transaction type.

        Args:
            transaction_type: Type of transaction to sum

        Returns:
            Total amount for the transaction type
        """
        try:
            stmt = select(func.sum(Transaction.total_amount)).where(
                Transaction.transaction_type == transaction_type
            )

            result = self.db.execute(stmt)
            total = result.scalar() or Decimal("0")

            return total

        except Exception as e:
            database_logger.error(
                "total_by_type_calculation_failed",
                transaction_type=transaction_type.value,
                error=str(e),
            )
            raise

    @log_database_operation("read")
    def get_recent_transactions(self, limit: int = 10) -> List[Transaction]:
        """
        Get recent transactions ordered by date.

        Args:
            limit: Maximum number of transactions to return

        Returns:
            List of recent transactions
        """
        try:
            stmt = (
                select(Transaction)
                .order_by(Transaction.date.desc())
                .limit(limit)
            )

            result = self.db.execute(stmt)
            transactions = result.scalars().all()

            return transactions

        except Exception as e:
            database_logger.error(
                "recent_transactions_retrieval_failed",
                limit=limit,
                error=str(e),
            )
            raise
