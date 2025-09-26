from fastapi import APIRouter

api_router = APIRouter()

from .routes import receipts, transactions

api_router.include_router(receipts.router)
api_router.include_router(transactions.router)
