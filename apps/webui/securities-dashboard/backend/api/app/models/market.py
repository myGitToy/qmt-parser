"""Market data models"""

from datetime import datetime as dt_datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


class Quote(BaseModel):
    """实时行情报价"""

    model_config = ConfigDict(
        json_encoders={Decimal: str},
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    symbol: str = Field(..., description="股票代码")
    name: Optional[str] = Field(None, description="股票名称")
    price: Decimal = Field(..., description="最新价")
    change: Decimal = Field(..., description="涨跌额")
    change_pct: Decimal = Field(..., description="涨跌幅(%)")
    volume: Optional[int] = Field(None, description="成交量")
    amount: Optional[Decimal] = Field(None, description="成交额")
    high: Optional[Decimal] = Field(None, description="最高价")
    low: Optional[Decimal] = Field(None, description="最低价")
    open_price: Optional[Decimal] = Field(None, description="开盘价", alias="open")
    close_prev: Optional[Decimal] = Field(None, description="昨收价")
    timestamp: dt_datetime = Field(default_factory=dt_datetime.now, description="更新时间")
    market: Optional[str] = Field(None, description="市场代码(SH/SZ)")


class Bar(BaseModel):
    """K线数据"""

    model_config = ConfigDict(
        json_encoders={Decimal: str},
        str_strip_whitespace=True,
    )

    symbol: str = Field(..., description="股票代码")
    timeframe: str = Field(..., description="周期(1min/5min/daily等)")
    dt: dt_datetime = Field(..., description="时间", alias="datetime")
    open_price: Decimal = Field(..., description="开盘价", alias="open")
    high: Decimal = Field(..., description="最高价")
    low: Decimal = Field(..., description="最低价")
    close: Decimal = Field(..., description="收盘价")
    volume: int = Field(..., description="成交量")
    amount: Optional[Decimal] = Field(None, description="成交额")


class MarketIndex(BaseModel):
    """市场指数"""

    model_config = ConfigDict(
        json_encoders={Decimal: str},
        str_strip_whitespace=True,
    )

    code: str = Field(..., description="指数代码")
    name: str = Field(..., description="指数名称")
    price: Decimal = Field(..., description="最新点位")
    change: Decimal = Field(..., description="涨跌点")
    change_pct: Decimal = Field(..., description="涨跌幅(%)")
    volume: Optional[int] = Field(None, description="成交量")
    amount: Optional[Decimal] = Field(None, description="成交额")
    timestamp: dt_datetime = Field(default_factory=dt_datetime.now)


class MarketOverview(BaseModel):
    """市场概览"""

    model_config = ConfigDict(
        json_encoders={Decimal: str},
        str_strip_whitespace=True,
    )

    indexes: List[Quote] = Field(default_factory=list, description="主要指数")
    market_status: str = Field(..., description="市场状态(开市/休市)")
    timestamp: dt_datetime = Field(default_factory=dt_datetime.now)
