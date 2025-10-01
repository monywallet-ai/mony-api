from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.crud.transaction import transaction_crud
from app.core.rate_limiter import general_rate_limit
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
    TransactionListResponse,
    TransactionSummary,
    TransactionType,
)
from app.models.transaction import TransactionType as ModelTransactionType

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post(
    "/",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new transaction",
    description="Create a new financial transaction with all the necessary details.",
)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
    _: None = Depends(general_rate_limit),
) -> TransactionResponse:
    """
    Create a new transaction with the following information:

    - **transaction_type**: Type of transaction (expense, income, saving, investment)
    - **merchant**: Name of the merchant or entity
    - **date**: Date when the transaction occurred
    - **total_amount**: Total amount of the transaction
    - **currency**: Currency code (default: USD)
    - **payment_method**: Method of payment used (optional)
    - **category**: Category for organization (optional)
    - **description**: Additional details (optional)
    - **reference_number**: Receipt or reference number (optional)
    - **taxes**: Tax amount if applicable (optional)
    - **items**: List of individual items in the transaction (optional)
    """
    result = transaction_crud.create(db=db, transaction_data=transaction)
    return result


@router.get(
    "/",
    response_model=TransactionListResponse,
    summary="Get all transactions",
    description="Retrieve a list of transactions with optional filtering and pagination.",
)
def get_transactions(
    skip: int = Query(0, ge=0, description="Number of transactions to skip"),
    limit: int = Query(
        20, ge=1, le=100, description="Number of transactions to return"
    ),
    transaction_type: Optional[TransactionType] = Query(
        None, description="Filter by transaction type"
    ),
    category: Optional[str] = Query(None, description="Filter by category"),
    merchant: Optional[str] = Query(None, description="Filter by merchant name"),
    date_from: Optional[date] = Query(
        None, description="Start date filter (YYYY-MM-DD)"
    ),
    date_to: Optional[date] = Query(None, description="End date filter (YYYY-MM-DD)"),
    currency: Optional[str] = Query(None, description="Filter by currency code"),
    sort_by: str = Query(
        "date", description="Field to sort by (date, total_amount, merchant, etc.)"
    ),
    sort_order: str = Query("desc", description="Sort order (asc or desc)"),
    db: Session = Depends(get_db),
    _: None = Depends(general_rate_limit),
) -> TransactionListResponse:
    """
    Get a paginated list of transactions with optional filtering:

    - **Pagination**: Use skip and limit parameters
    - **Filters**: Filter by type, category, merchant, date range, currency
    - **Sorting**: Sort by any field in ascending or descending order
    """
    # Convert string transaction_type to enum if provided
    model_transaction_type = None
    if transaction_type:
        model_transaction_type = ModelTransactionType(transaction_type.value)

    transactions = transaction_crud.get_multi(
        db=db,
        skip=skip,
        limit=limit,
        transaction_type=model_transaction_type,
        category=category,
        merchant=merchant,
        date_from=date_from,
        date_to=date_to,
        currency=currency,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    # Get total count for pagination info
    total_transactions = transaction_crud.get_multi(
        db=db,
        skip=0,
        limit=1000000,  # Large number to get all for counting
        transaction_type=model_transaction_type,
        category=category,
        merchant=merchant,
        date_from=date_from,
        date_to=date_to,
        currency=currency,
    )

    return TransactionListResponse(
        transactions=transactions, total=len(total_transactions), skip=skip, limit=limit
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Get a specific transaction",
    description="Retrieve a specific transaction by its ID.",
)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(general_rate_limit),
) -> TransactionResponse:
    """
    Get a specific transaction by ID.

    Returns detailed information about the transaction including all items.
    """
    transaction = transaction_crud.get(db=db, transaction_id=transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )
    return transaction


@router.put(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Update a transaction",
    description="Update an existing transaction with new information.",
)
def update_transaction(
    transaction_id: int,
    transaction_update: TransactionUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(general_rate_limit),
) -> TransactionResponse:
    """
    Update an existing transaction.

    You can update any field of the transaction. Only provided fields will be updated.
    """
    # Convert TransactionUpdate to TransactionCreate for the CRUD operation
    # This is a workaround since our CRUD expects TransactionCreate
    update_data = transaction_update.model_dump(exclude_unset=True)

    # Get the existing transaction to fill in missing fields
    existing_transaction = transaction_crud.get(db=db, transaction_id=transaction_id)
    if not existing_transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )

    # Create a full TransactionCreate object with updated values
    full_data = {
        "transaction_type": update_data.get(
            "transaction_type", existing_transaction.transaction_type
        ),
        "merchant": update_data.get("merchant", existing_transaction.merchant),
        "date": update_data.get("date", existing_transaction.date),
        "total_amount": update_data.get(
            "total_amount", existing_transaction.total_amount
        ),
        "currency": update_data.get("currency", existing_transaction.currency),
        "payment_method": update_data.get(
            "payment_method", existing_transaction.payment_method
        ),
        "category": update_data.get("category", existing_transaction.category),
        "description": update_data.get("description", existing_transaction.description),
        "reference_number": update_data.get(
            "reference_number", existing_transaction.reference_number
        ),
        "taxes": update_data.get("taxes", existing_transaction.taxes),
        "items": update_data.get("items", existing_transaction.items or []),
    }

    transaction_full_update = TransactionCreate(**full_data)

    updated_transaction = transaction_crud.update(
        db=db, transaction_id=transaction_id, transaction_update=transaction_full_update
    )

    if not updated_transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )

    return updated_transaction


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a transaction",
    description="Delete a specific transaction by its ID.",
)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(general_rate_limit),
):
    """
    Delete a transaction permanently.

    This action cannot be undone.
    """
    success = transaction_crud.delete(db=db, transaction_id=transaction_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )


@router.get(
    "/summary/monthly",
    response_model=TransactionSummary,
    summary="Get monthly transaction summary",
    description="Get a summary of transactions for a specific month and year.",
)
def get_monthly_summary(
    year: int = Query(..., description="Year (e.g., 2024)"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    db: Session = Depends(get_db),
    _: None = Depends(general_rate_limit),
) -> TransactionSummary:
    """
    Get a comprehensive summary of transactions for a specific month:

    - **Total amounts** by transaction type (expenses, income, savings, investments)
    - **Transaction count** for the month
    - **Category breakdown** showing amounts per category
    """
    summary_data = transaction_crud.get_monthly_summary(db=db, year=year, month=month)
    return TransactionSummary(**summary_data)


@router.get(
    "/search/",
    response_model=List[TransactionResponse],
    summary="Search transactions",
    description="Search transactions by merchant, description, category, or reference number.",
)
def search_transactions(
    q: str = Query(..., min_length=2, description="Search term (minimum 2 characters)"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of results"),
    db: Session = Depends(get_db),
    _: None = Depends(general_rate_limit),
) -> List[TransactionResponse]:
    """
    Search transactions by text across multiple fields:

    - **Merchant name**
    - **Description**
    - **Category**
    - **Reference number**

    Returns up to the specified limit of matching transactions.
    """
    return transaction_crud.search(db=db, search_term=q, limit=limit)


@router.get(
    "/stats/by-type",
    summary="Get transaction totals by type",
    description="Get total amounts for each transaction type.",
)
def get_totals_by_type(
    db: Session = Depends(get_db),
    _: None = Depends(general_rate_limit),
) -> dict:
    """
    Get total amounts grouped by transaction type.

    Returns totals for expenses, income, savings, and investments.
    """
    totals = {}
    for transaction_type in ModelTransactionType:
        total = transaction_crud.get_total_by_type(
            db=db, transaction_type=transaction_type
        )
        totals[transaction_type.value] = total

    return {
        "totals": totals,
        "net_worth": totals.get("income", 0)
        - totals.get("expense", 0)
        + totals.get("saving", 0)
        + totals.get("investment", 0),
    }
