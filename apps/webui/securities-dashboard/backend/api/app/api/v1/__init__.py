"""API v1 routes"""

from fastapi import APIRouter

from .market import router as market_router
from .portfolio import router as portfolio_router

api_router = APIRouter(prefix="/v1")

api_router.include_router(market_router, prefix="/market", tags=["market"])
api_router.include_router(portfolio_router, prefix="/portfolio", tags=["portfolio"])

__all__ = ["api_router"]
