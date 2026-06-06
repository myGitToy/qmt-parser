"""API v1 routes"""

from fastapi import APIRouter

from .market import router as market_router
from .portfolio import router as portfolio_router

# 注意：不要在这里添加 /v1 前缀，因为它已经在 main.py 中通过 settings.api_prefix="/api/v1" 设置了
api_router = APIRouter()

api_router.include_router(market_router, prefix="/market", tags=["market"])
api_router.include_router(portfolio_router, prefix="/portfolio", tags=["portfolio"])

__all__ = ["api_router"]
