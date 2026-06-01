"""Market data models"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class Quote(BaseModel):
    """实时行情报价"""

    symbol: str = Field(..., description="股票代码")
    name: Optional[str] = Field(None, description="股票名称")
    price: Decimal = Field(..., description="最新价")
    change: Decimal = Field(..., description="涨跌额")
    change_pct: Decimal = Field(..., description="涨跌幅(%)")
    volume: Optional[int] = Field(None, description="成交量")
    amount: Optional[Decimal] = Field(None, description="成交额")
    high: Optional[Decimal] = Field(None, description="最高价")
    low: Optional[Decimal] = Field(None, description="最低价")
    open: Optional[Decimal] = Field(None, description="开盘价")
    close_prev: Optional[Decimal] = Field(None, description="昨收价")
    timestamp: datetime = Field(default_factory=datetime.now, description="更新时间")
    market: Optional[str] = Field(None, description="市场代码(SH/SZ)")

    class Config:
        json_encoders = {
            Decimal: str,
        }


class Bar(BaseModel):
    """K线数据"""

    symbol: str = Field(..., description="股票代码")
    timeframe: str = Field(..., description="周期(1min/5min/daily等)")
    datetime: datetime = Field(..., description="时间")
    open: Decimal = Field(..., description="开盘价")
    high: Decimal = Field(..., description="最高价")
    low: Decimal = Field(..., description="最低价")
    close: Decimal = Field(..., description="收盘价")
    volume: int = Field(..., description="成交量")
    amount: Optional[Decimal] = Field(None, description="成交额")

    class Config:
        json_encoders = {
            Decimal: str,
        }


class MarketIndex(BaseModel):
    """市场指数"""

    code: str = Field(..., description="指数代码")
    name: str = Field(..., description="指数名称")
    price: Decimal = Field(..., description="最新点位")
    change: Decimal = Field(..., description="涨跌点")
    change_pct: Decimal = Field(..., description="涨跌幅(%)")
    volume: Optional[int] = Field(None, description="成交量")
    amount: Optional[Decimal] = Field(None, description="成交额")
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            Decimal: str,
        }


class MarketOverview(BaseModel):
    """市场概览"""

    indexes: list[MarketIndex] = Field(default_factory=list, description="主要指数")
    market_status: str = Field(..., description="市场状态(开市/休市)")
    timestamp: datetime = Field(default_factory=datetime.now)
