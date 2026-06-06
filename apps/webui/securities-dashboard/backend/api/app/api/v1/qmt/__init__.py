"""
QMT数据校验 API路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Literal
from app.services.qmt_service import QmtDataService

# 输入验证常量
VALID_MARKETS = ["SH", "SZ", "BJ", "SZO", "SHO"]
VALID_FINANCE_TYPES = ["7001", "7002", "7003", "7004", "7005", "7006", "7007", "7008"]

router = APIRouter()


# 依赖注入：获取QMT服务实例
def get_qmt_service() -> QmtDataService:
    """获取QMT数据服务实例"""
    return QmtDataService()


@router.get("/status")
async def get_qmt_status(service: QmtDataService = Depends(get_qmt_service)) -> Dict[str, Any]:
    """
    获取QMT路径配置状态

    检查QMT客户端路径和datadir是否配置正确
    """
    return service.validate_path()


@router.get("/summary")
async def get_qmt_summary(service: QmtDataService = Depends(get_qmt_service)) -> Dict[str, Any]:
    """
    获取QMT数据总览

    返回市场数、文件数、总大小等统计信息
    """
    return service.get_summary()


@router.get("/markets")
async def list_markets(service: QmtDataService = Depends(get_qmt_service)) -> Dict[str, Any]:
    """
    列出所有市场

    返回可用的市场列表(SH/SZ/BJ等)
    """
    markets = service.list_markets()
    return {
        "markets": markets,
        "total": len(markets)
    }


@router.get("/markets/{market}/periods")
async def list_periods(
    market: str,
    service: QmtDataService = Depends(get_qmt_service)
) -> Dict[str, Any]:
    """
    列出指定市场的所有周期

    - **market**: 市场代码 (SH/SZ/BJ等)
    """
    periods = service.list_periods(market)
    return {
        "market": market,
        "periods": periods,
        "total": len(periods)
    }


@router.get("/markets/{market}/periods/{period}/files")
async def list_files(
    market: str,
    period: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=1000, description="每页大小"),
    service: QmtDataService = Depends(get_qmt_service)
) -> Dict[str, Any]:
    """
    列出指定市场、周期下的文件

    - **market**: 市场代码 (SH/SZ/BJ等)
    - **period**: 周期代码 (0/60/300/86400等)
    - **page**: 页码 (从1开始)
    - **page_size**: 每页大小 (最大1000)
    """
    result = service.list_files(market, period, page, page_size)
    if not result.get("valid"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


@router.get("/file-info")
async def get_file_info(
    path: str = Query(..., description="文件路径(相对于datadir)"),
    service: QmtDataService = Depends(get_qmt_service)
) -> Dict[str, Any]:
    """
    获取单个文件的详细信息

    - **path**: 文件路径，相对于datadir (如: SH/86400/000001.DAT)
    """
    result = service.get_file_info(path)
    if not result.get("valid"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


@router.get("/other-files")
async def get_other_files(service: QmtDataService = Depends(get_qmt_service)) -> Dict[str, Any]:
    """
    获取其他QMT文件信息

    返回财务数据、分红数据、节假日等文件信息
    """
    return service.scan_other_files()


# ============================================================
# 财务数据 API
# ============================================================

@router.get("/finance/types")
async def list_finance_types(service: QmtDataService = Depends(get_qmt_service)) -> Dict[str, Any]:
    """
    列出所有财务数据类型

    返回各财务报表类型（资产负债表、利润表等）的文件统计
    """
    types = service.list_finance_types()
    return {
        "types": types,
        "total": len(types),
    }


@router.get("/finance/{finance_type}/markets/{market}/files")
async def list_finance_files(
    finance_type: str,
    market: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=1000, description="每页大小"),
    service: QmtDataService = Depends(get_qmt_service),
) -> Dict[str, Any]:
    """
    列出指定财务类型和市场的文件

    - **finance_type**: 财务类型代码 (7001-7008)
    - **market**: 市场代码 (SH/SZ/BJ等)
    """
    if finance_type not in VALID_FINANCE_TYPES:
        raise HTTPException(status_code=400, detail=f"无效的财务类型: {finance_type}")
    if market not in VALID_MARKETS:
        raise HTTPException(status_code=400, detail=f"无效的市场代码: {market}")
    result = service.list_finance_files(finance_type, market, page, page_size)
    if not result.get("valid"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


# ============================================================
# 分笔成交 (Tick) API
# ============================================================

@router.get("/tick/markets/{market}/stocks")
async def list_tick_stocks(
    market: str,
    service: QmtDataService = Depends(get_qmt_service),
) -> Dict[str, Any]:
    """
    列出指定市场下有Tick分笔数据的股票代码

    - **market**: 市场代码 (SH/SZ/BJ等)
    """
    if market not in VALID_MARKETS:
        raise HTTPException(status_code=400, detail=f"无效的市场代码: {market}")
    stocks = service.list_tick_stocks(market)
    return {
        "market": market,
        "stocks": stocks,
        "total": len(stocks),
    }


# ============================================================
# ETF申赎 API
# ============================================================

@router.get("/etf/markets/{market}/codes")
async def list_etf_codes(
    market: str,
    service: QmtDataService = Depends(get_qmt_service),
) -> Dict[str, Any]:
    """
    列出指定市场的ETF代码

    - **market**: 市场代码 (SH/SZ)
    """
    if market not in VALID_MARKETS:
        raise HTTPException(status_code=400, detail=f"无效的市场代码: {market}")
    codes = service.list_etf_codes(market)
    return {
        "market": market,
        "codes": codes,
        "total": len(codes),
    }


@router.get("/etf/markets/{market}/codes/{code}/files")
async def list_etf_files(
    market: str,
    code: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=1000, description="每页大小"),
    service: QmtDataService = Depends(get_qmt_service),
) -> Dict[str, Any]:
    """
    列出指定ETF的申赎清单文件

    - **market**: 市场代码
    - **code**: ETF代码
    """
    if market not in VALID_MARKETS:
        raise HTTPException(status_code=400, detail=f"无效的市场代码: {market}")
    result = service.list_etf_files(market, code, page, page_size)
    if not result.get("valid"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


# ============================================================
# 除权数据 API
# ============================================================

@router.get("/dividend/markets/{market}/files")
async def list_dividend_files(
    market: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=1000, description="每页大小"),
    service: QmtDataService = Depends(get_qmt_service),
) -> Dict[str, Any]:
    """
    列出除权数据文件

    - **market**: 市场代码 (SH/SZ/BJ等)
    """
    if market not in VALID_MARKETS:
        raise HTTPException(status_code=400, detail=f"无效的市场代码: {market}")
    result = service.list_dividend_files(market, page, page_size)
    if not result.get("valid"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


# ============================================================
# 板块分类数据 API
# ============================================================

@router.get("/sector/categories")
async def list_sector_categories(
    service: QmtDataService = Depends(get_qmt_service),
) -> Dict[str, Any]:
    """
    列出所有板块分类类别

    返回 Sector/ 下的子目录列表，如申万行业、证监会行业、概念板块等
    """
    categories = service.list_sector_categories()
    return {
        "categories": categories,
        "total": len(categories),
    }


@router.get("/sector/categories/{category}/files")
async def list_sector_files(
    category: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=1000, description="每页大小"),
    service: QmtDataService = Depends(get_qmt_service),
) -> Dict[str, Any]:
    """
    列出指定板块分类下的板块文件

    - **category**: 板块分类目录名（如 申万一级行业板块、D概念）
    """
    if "/" in category or "\\" in category or ".." in category:
        raise HTTPException(status_code=400, detail="无效的板块分类名")
    result = service.list_sector_files(category, page, page_size)
    if not result.get("valid"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result
