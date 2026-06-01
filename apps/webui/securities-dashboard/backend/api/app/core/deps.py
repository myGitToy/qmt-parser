"""
依赖注入
"""

from functools import lru_cache

from ..services.market_service import DataSourceManager
from .config import Settings, get_settings


@lru_cache
def get_data_source_config() -> dict:
    """
    获取数据源配置

    Returns:
        dict: 配置字典
    """
    settings = get_settings()
    return {
        "tushare_token": settings.tushare_token,
        "storage_type": "hdf5",
        "hdf5_path": "C:/Data/hdf5",
        "mysql_url": None,
        "vendor_priority": ["local", "tushare", "akshare"],
    }


async def get_data_manager() -> DataSourceManager:
    """
    获取数据管理器实例

    Returns:
        DataSourceManager: 数据管理器实例
    """
    config = get_data_source_config()
    return DataSourceManager(config)
