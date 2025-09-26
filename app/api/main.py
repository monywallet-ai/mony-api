from fastapi import APIRouter

api_router = APIRouter()

from .routes import receipts

api_router.include_router(receipts.router)
