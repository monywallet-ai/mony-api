from typing import List, Optional, Dict, Any
from datetime import date
from decimal import Decimal

from app.repositories.transaction_repository import TransactionRepository
from app.models.transaction import Transaction, TransactionType as ModelTransactionType
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionListResponse,
)
from app.core.logging import general_logger


class TransactionService:
    """
    Service class for transaction business logic.

    Provides high-level operations for transactions, coordinating
    between repositories and implementing business rules.
    """

    def __init__(self, transaction_repository: TransactionRepository):
        """
        Initialize the transaction service.

        Args:
            transaction_repository: Repository for transaction data access
        """
        self.transaction_repo = transaction_repository

    def create_transaction(self, transaction_data: TransactionCreate) -> Transaction:
        """
        Create a new transaction.

        Args:
            transaction_data: Transaction creation data

        Returns:
            Created transaction

        Raises:
            ValueError: If business rules are violated
        """
        try:
            # Business logic validation
            self._validate_transaction_data(transaction_data)

            # Create transaction
            transaction = self.transaction_repo.create(transaction_data)

            general_logger.info(
                "transaction_created",
                transaction_id=transaction.id,
                merchant=transaction.merchant,
                amount=float(transaction.total_amount),
            )

            return transaction

        except Exception as e:
            general_logger.error(
                "transaction_creation_failed",
                error=str(e),
                merchant=transaction_data.merchant if transaction_data else None,
            )
            raise

    def get_transaction_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """
        Get transaction by ID with items.

        Args:
            transaction_id: Transaction ID

        Returns:
            Transaction with items or None if not found
        """
        try:
            transaction = self.transaction_repo.get_by_id_with_items(transaction_id)

            return transaction

        except Exception as e:
            general_logger.error(
                "transaction_retrieval_failed",
                transaction_id=transaction_id,
                error=str(e),
            )
            raise

    def get_transactions_paginated(
        self,
        skip: int = 0,
        limit: int = 20,
        transaction_type: Optional[ModelTransactionType] = None,
        category: Optional[str] = None,
        merchant: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        currency: Optional[str] = None,
        sort_by: str = "date",
        sort_order: str = "desc",
    ) -> TransactionListResponse:
        """
        Get paginated transactions with filtering.

        Args:
            skip: Number of transactions to skip
            limit: Maximum number of transactions to return
            transaction_type: Filter by transaction type
            category: Filter by category
            merchant: Filter by merchant name
            date_from: Start date filter
            date_to: End date filter
            currency: Filter by currency
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)

        Returns:
            Paginated transaction response
        """
        try:
            # Validate pagination parameters
            if skip < 0:
                skip = 0
            if limit > 100:
                limit = 100
            if limit < 1:
                limit = 20

            # Get transactions
            transactions = self.transaction_repo.get_filtered_transactions(
                skip=skip,
                limit=limit,
                transaction_type=transaction_type,
                category=category,
                merchant=merchant,
                date_from=date_from,
                date_to=date_to,
                currency=currency,
                sort_by=sort_by,
                sort_order=sort_order,
            )

            # Get total count for pagination
            try:
                total = self.transaction_repo.count()
            except Exception:
                # Fallback to length of current results if count fails
                total = len(transactions)

            response = TransactionListResponse(
                transactions=transactions, total=total, skip=skip, limit=limit
            )

            return response

        except Exception as e:
            general_logger.error(
                "transactions_pagination_failed", skip=skip, limit=limit, error=str(e)
            )
            raise

    def update_transaction(
        self, transaction_id: int, transaction_update: TransactionUpdate
    ) -> Optional[Transaction]:
        """
        Update an existing transaction.

        Args:
            transaction_id: Transaction ID
            transaction_update: Update data

        Returns:
            Updated transaction or None if not found
        """
        try:
            # Business logic validation for updates
            if transaction_update.total_amount is not None:
                self._validate_amount(transaction_update.total_amount)

            # Update transaction
            transaction = self.transaction_repo.update(
                transaction_id, transaction_update
            )

            if transaction:
                general_logger.info(
                    "transaction_updated",
                    transaction_id=transaction_id,
                    updated_fields=list(
                        transaction_update.model_dump(exclude_unset=True).keys()
                    ),
                )

            return transaction

        except Exception as e:
            general_logger.error(
                "transaction_update_failed", transaction_id=transaction_id, error=str(e)
            )
            raise

    def delete_transaction(self, transaction_id: int) -> bool:
        """
        Delete a transaction.

        Args:
            transaction_id: Transaction ID

        Returns:
            True if deleted, False if not found
        """
        try:
            deleted = self.transaction_repo.delete(transaction_id)

            if deleted:
                general_logger.info(
                    "transaction_deleted", transaction_id=transaction_id
                )

            return deleted

        except Exception as e:
            general_logger.error(
                "transaction_deletion_failed",
                transaction_id=transaction_id,
                error=str(e),
            )
            raise

    def search_transactions(
        self, search_term: str, limit: int = 20
    ) -> List[Transaction]:
        """
        Search transactions by text.

        Args:
            search_term: Text to search for
            limit: Maximum number of results

        Returns:
            List of matching transactions
        """
        try:
            # Validate search term
            if not search_term or len(search_term.strip()) < 2:
                raise ValueError("Search term must be at least 2 characters long")

            transactions = self.transaction_repo.search_transactions(
                search_term.strip(), limit
            )

            return transactions

        except Exception as e:
            general_logger.error(
                "transaction_search_failed", search_term=search_term, error=str(e)
            )
            raise

    def get_monthly_summary(self, year: int, month: int) -> Dict[str, Any]:
        """
        Get monthly transaction summary.

        Args:
            year: Year
            month: Month (1-12)

        Returns:
            Monthly summary data
        """
        try:
            # Validate parameters
            if month < 1 or month > 12:
                raise ValueError("Month must be between 1 and 12")

            summary = self.transaction_repo.get_monthly_summary(year, month)

            return summary

        except Exception as e:
            general_logger.error(
                "monthly_summary_failed", year=year, month=month, error=str(e)
            )
            raise

    def get_totals_by_type(self) -> Dict[str, float]:
        """
        Get total amounts by transaction type.

        Returns:
            Dictionary with totals by transaction type
        """
        try:
            totals = {}

            for transaction_type in ModelTransactionType:
                total = self.transaction_repo.get_total_by_type(transaction_type)
                totals[transaction_type.value] = float(total)

            # Calculate net worth
            net_worth = (
                totals.get("income", 0)
                - totals.get("expense", 0)
                + totals.get("saving", 0)
                + totals.get("investment", 0)
            )

            result = {"totals": totals, "net_worth": net_worth}

            return result

        except Exception as e:
            general_logger.error("totals_by_type_calculation_failed", error=str(e))
            raise

    def get_recent_transactions(self, limit: int = 10) -> List[Transaction]:
        """
        Get recent transactions.

        Args:
            limit: Maximum number of transactions

        Returns:
            List of recent transactions
        """
        try:
            if limit > 50:
                limit = 50  # Reasonable limit

            transactions = self.transaction_repo.get_recent_transactions(limit)

            return transactions

        except Exception as e:
            general_logger.error(
                "recent_transactions_retrieval_failed", limit=limit, error=str(e)
            )
            raise

    def _validate_transaction_data(self, transaction_data: TransactionCreate) -> None:
        """
        Validate transaction data according to business rules.

        Args:
            transaction_data: Transaction data to validate

        Raises:
            ValueError: If validation fails
        """
        # Validate amount
        self._validate_amount(transaction_data.total_amount)

        # Validate merchant name
        if not transaction_data.merchant or len(transaction_data.merchant.strip()) < 1:
            raise ValueError("Merchant name is required")

        # Add more business rule validations as needed
        # Example: Check for duplicate transactions, validate currency, etc.

    def _validate_amount(self, amount: Decimal) -> None:
        """
        Validate transaction amount.

        Args:
            amount: Amount to validate

        Raises:
            ValueError: If amount is invalid
        """
        if amount <= 0:
            raise ValueError("Transaction amount must be greater than 0")

        if amount > Decimal("1000000"):  # 1 million limit
            raise ValueError("Transaction amount exceeds maximum allowed limit")

        # Check decimal places (should be 2 for currency)
        if amount.as_tuple().exponent < -2:
            raise ValueError(
                "Transaction amount cannot have more than 2 decimal places"
            )
