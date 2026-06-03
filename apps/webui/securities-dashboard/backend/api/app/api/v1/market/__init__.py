"""Market data API routes"""

from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
from typing import Dict

from app.models.market import Bar, Quote, MarketOverview
from app.providers.base import MarketDataProvider
from app.providers.tushare_provider import TushareProvider
from app.providers.akshare_provider import AKShareProvider

router = APIRouter()


# 依赖注入：获取数据提供者
async def get_market_provider() -> MarketDataProvider:
    """获取市场数据提供者"""
    from app.core.config import settings

    # 优先使用 Tushare
    if settings.tushare_enabled and settings.tushare_token:
        try:
            provider = TushareProvider(settings.tushare_token)
            return provider
        except Exception as e:
            # Tushare 初始化失败，降级到 AKShare
            print(f"⚠️ Tushare 初始化失败: {str(e)}，降级使用 AKShare")
            return AKShareProvider()
    else:
        # 使用 AKShare
        return AKShareProvider()


@router.get("/health")
async def health_check() -> Dict[str, any]:
    """
    健康检查端点

    返回服务状态和数据源配置信息
    """
    from app.core.config import settings

    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "providers": {
            "tushare": {
                "enabled": settings.tushare_enabled,
                "configured": bool(settings.tushare_token and settings.tushare_token.strip()),
                "token_preview": f"{settings.tushare_token[:8]}..." if settings.tushare_token and len(settings.tushare_token) > 8 else None,
            },
            "akshare": {
                "enabled": settings.akshare_enabled,
                "available": True,  # AKShare 始终可用
            },
        },
        "warnings": [],
    }

    # 添加警告信息
    if not settings.tushare_token or not settings.tushare_token.strip():
        health_status["warnings"].append({
            "type": "tushare_not_configured",
            "message": "Tushare Token 未配置，系统将使用 AKShare 作为数据源（功能可能受限）",
            "solution": "请在 .env 文件中设置 TUSHARE_TOKEN 环境变量"
        })
    elif len(settings.tushare_token) < 30:
        health_status["warnings"].append({
            "type": "tushare_token_invalid",
            "message": "Tushare Token 格式可能不正确（长度过短）",
            "solution": "请检查 TUSHARE_TOKEN 是否正确配置"
        })

    return health_status


@router.get("/overview", response_model=MarketOverview)
async def get_market_overview(
    provider: MarketDataProvider = Depends(get_market_provider),
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
    indexes = await provider.get_market_indexes()

    return MarketOverview(
        indexes=[Quote.model_validate(idx) for idx in indexes],
        market_status=market_status,
        timestamp=now,
    )


@router.get("/quote/{symbol}", response_model=Quote)
async def get_realtime_quote(
    symbol: str,
    provider: MarketDataProvider = Depends(get_market_provider),
) -> Quote:
    """
    获取实时行情报价

    - **symbol**: 股票代码，如 "000001.SZ" 或 "600000.SH"
    """
    try:
        return await provider.get_realtime_quote(symbol)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取行情失败: {str(e)}")


@router.post("/quote/batch", response_model=list[Quote])
async def get_batch_quotes(
    symbols: list[str],
    provider: MarketDataProvider = Depends(get_market_provider),
) -> list[Quote]:
    """
    批量获取实时行情报价

    - **symbols**: 股票代码列表
    """
    quotes = []
    for symbol in symbols:
        try:
            quote = await provider.get_realtime_quote(symbol)
            quotes.append(quote)
        except Exception:
            continue  # 跳过失败的股票
    return quotes


@router.get("/bars/{symbol}", response_model=list[Bar])
async def get_historical_bars(
    symbol: str,
    timeframe: str = Query("daily", description="K线周期"),
    start_date: datetime = Query(
        default=datetime.now() - timedelta(days=365),
        description="开始日期",
    ),
    end_date: datetime = Query(
        default=datetime.now(),
        description="结束日期",
    ),
    limit: int = Query(1000, ge=1, le=5000, description="返回条数限制"),
    provider: MarketDataProvider = Depends(get_market_provider),
) -> list[Bar]:
    """
    获取历史K线数据

    - **symbol**: 股票代码，如 "000001.SZ" 或 "600000.SH"
    - **timeframe**: K线周期 (1min/5min/15min/30min/60min/daily/weekly/monthly)
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    - **limit**: 返回条数限制
    """
    try:
        bars = await provider.get_historical_bars(symbol, timeframe, start_date, end_date)
        # 限制返回条数并按时间排序
        bars = sorted(bars, key=lambda x: x.datetime, reverse=False)[-limit:]
        return bars
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotImplementedError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取K线数据失败: {str(e)}")


@router.get("/indexes", response_model=list[Quote])
async def get_market_indexes(
    provider: MarketDataProvider = Depends(get_market_provider),
) -> list[Quote]:
    """
    获取市场主要指数

    返回上证指数、深证成指、创业板指等主要指数
    """
    try:
        indexes = await provider.get_market_indexes()
        return [Quote.model_validate(idx) for idx in indexes]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取指数失败: {str(e)}")


@router.get("/search", response_model=list[dict])
async def search_stocks(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    provider: MarketDataProvider = Depends(get_market_provider),
) -> list[dict]:
    """
    搜索股票

    - **keyword**: 搜索关键词（代码或名称）
    """
    try:
        return await provider.search_stocks(keyword)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")
