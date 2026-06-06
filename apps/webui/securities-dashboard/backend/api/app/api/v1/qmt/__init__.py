"""
QMT数据校验 API路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any
from app.services.qmt_service import QmtDataService

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
