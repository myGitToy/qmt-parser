"""Market data API routes"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ...core.deps import get_data_manager
from ...services.market_service import DataSourceManager
from ....vendor.base import KType

router = APIRouter()

# ============ Response Models ============


class MarketIndex(BaseModel):
    """市场指数"""
    code: str = Field(..., description="指数代码")
    name: str = Field(..., description="指数名称")
    price: float = Field(..., description="最新点位")
    change: float = Field(..., description="涨跌点")
    change_pct: float = Field(..., description="涨跌幅(%)")
    volume: Optional[float] = Field(None, description="成交量")
    amount: Optional[float] = Field(None, description="成交额")
    timestamp: str = Field(..., description="更新时间")


class QuoteData(BaseModel):
    """实时行情报价"""
    symbol: str = Field(..., description="股票代码")
    name: Optional[str] = Field(None, description="股票名称")
    price: float = Field(..., description="最新价")
    change: float = Field(..., description="涨跌额")
    change_pct: float = Field(..., description="涨跌幅(%)")
    volume: Optional[float] = Field(None, description="成交量")
    amount: Optional[float] = Field(None, description="成交额")
    high: Optional[float] = Field(None, description="最高价")
    low: Optional[float] = Field(None, description="最低价")
    open: Optional[float] = Field(None, description="开盘价")
    close_prev: Optional[float] = Field(None, description="昨收价")
    timestamp: str = Field(..., description="更新时间")
    market: Optional[str] = Field(None, description="市场代码")


class BarData(BaseModel):
    """K线数据"""
    symbol: str = Field(..., description="股票代码")
    timeframe: str = Field(..., description="周期")
    datetime: str = Field(..., description="时间")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: float = Field(..., description="成交量")
    amount: Optional[float] = Field(None, description="成交额")


class MarketOverview(BaseModel):
    """市场概览"""
    indexes: list[MarketIndex] = Field(default_factory=list, description="主要指数")
    market_status: str = Field(..., description="市场状态")
    timestamp: str = Field(..., description="更新时间")


class StockSearchResult(BaseModel):
    """股票搜索结果"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    market: str = Field(..., description="市场")


# ============ API Endpoints ============


@router.get("/overview", response_model=MarketOverview)
async def get_market_overview(
    manager: DataSourceManager = Depends(get_data_manager),
) -> MarketOverview:
    """
    获取市场概览

    返回主要指数和市场状态
    """
    # 判断市场状态
    now = datetime.now()
    is_weekend = now.weekday() >= 5  # 周六、周日
    is_trading_time = 9 <= now.hour < 15  # 交易时间

    if is_weekend or not is_trading_time:
        market_status = "休市"
    else:
        market_status = "开市"

    # 获取主要指数
    indexes_data = await manager.get_market_indexes()

    indexes = []
    for idx in indexes_data:
        indexes.append(
            MarketIndex(
                code=idx.get("symbol", ""),
                name=idx.get("name", ""),
                price=idx.get("price", 0),
                change=idx.get("change", 0),
                change_pct=idx.get("change_pct", 0),
                volume=idx.get("volume"),
                amount=idx.get("amount"),
                timestamp=idx.get("timestamp", now.isoformat()),
            )
        )

    return MarketOverview(
        indexes=indexes,
        market_status=market_status,
        timestamp=now.isoformat(),
    )


@router.get("/quote/{symbol}", response_model=QuoteData)
async def get_realtime_quote(
    symbol: str,
    manager: DataSourceManager = Depends(get_data_manager),
) -> QuoteData:
    """
    获取实时行情报价

    - **symbol**: 股票代码，如 "000001.SZ" 或 "600000.SH"
    """
    try:
        quote = await manager.get_realtime_quote(symbol)
        if not quote:
            raise HTTPException(status_code=404, detail=f"未找到股票 {symbol} 的数据")

        return QuoteData(**quote)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取行情失败: {str(e)}")


@router.post("/quote/batch", response_model=list[QuoteData])
async def get_batch_quotes(
    symbols: list[str],
    manager: DataSourceManager = Depends(get_data_manager),
) -> list[QuoteData]:
    """
    批量获取实时行情报价

    - **symbols**: 股票代码列表
    """
    quotes = []
    for symbol in symbols:
        try:
            quote = await manager.get_realtime_quote(symbol)
            if quote:
                quotes.append(QuoteData(**quote))
        except Exception:
            continue  # 跳过失败的股票
    return quotes


@router.get("/bars/{symbol}", response_model=list[BarData])
async def get_historical_bars(
    symbol: str,
    timeframe: str = Query("daily", description="K线周期"),
    start_date: Optional[datetime] = Query(
        None,
        description="开始日期",
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="结束日期",
    ),
    limit: int = Query(1000, ge=1, le=5000, description="返回条数限制"),
    manager: DataSourceManager = Depends(get_data_manager),
) -> list[BarData]:
    """
    获取历史K线数据

    - **symbol**: 股票代码，如 "000001.SZ" 或 "600000.SH"
    - **timeframe**: K线周期 (1min/5min/15min/30min/60min/daily/weekly/monthly)
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    - **limit**: 返回条数限制
    """
    try:
        # 解析K线类型
        try:
            ktype = KType(timeframe)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"不支持的K线周期: {timeframe}")

        # 设置默认日期范围
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = datetime.fromtimestamp(end_date.timestamp() - 365 * 24 * 3600)

        # 获取数据
        df = await manager.get_k_data(symbol, start_date, end_date, ktype)

        if df.empty:
            return []

        # 转换为响应模型
        bars = []
        for _, row in df.iterrows():
            bars.append(
                BarData(
                    symbol=row["symbol"],
                    timeframe=timeframe,
                    datetime=row["date"].isoformat(),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                    amount=float(row["amount"]) if "amount" in row and row["amount"] else None,
                )
            )

        # 限制返回条数
        bars = bars[-limit:] if len(bars) > limit else bars

        return bars

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取K线数据失败: {str(e)}")


@router.get("/indexes", response_model=list[MarketIndex])
async def get_market_indexes(
    manager: DataSourceManager = Depends(get_data_manager),
) -> list[MarketIndex]:
    """
    获取市场主要指数

    返回上证指数、深证成指、创业板指等主要指数
    """
    try:
        indexes_data = await manager.get_market_indexes()

        indexes = []
        for idx in indexes_data:
            indexes.append(
                MarketIndex(
                    code=idx.get("symbol", ""),
                    name=idx.get("name", ""),
                    price=idx.get("price", 0),
                    change=idx.get("change", 0),
                    change_pct=idx.get("change_pct", 0),
                    volume=idx.get("volume"),
                    amount=idx.get("amount"),
                    timestamp=idx.get("timestamp", datetime.now().isoformat()),
                )
            )

        return indexes

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取指数失败: {str(e)}")


@router.get("/search", response_model=list[StockSearchResult])
async def search_stocks(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    manager: DataSourceManager = Depends(get_data_manager),
) -> list[StockSearchResult]:
    """
    搜索股票

    - **keyword**: 搜索关键词（代码或名称）
    """
    try:
        results = await manager.search_stock(keyword)

        return [
            StockSearchResult(
                code=r.get("code", ""),
                name=r.get("name", ""),
                market=r.get("market", ""),
            )
            for r in results
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/providers/status")
async def get_providers_status(
    manager: DataSourceManager = Depends(get_data_manager),
) -> dict:
    """
    获取数据源状态

    返回各数据源的可用状态
    """
    return manager.get_provider_status()
