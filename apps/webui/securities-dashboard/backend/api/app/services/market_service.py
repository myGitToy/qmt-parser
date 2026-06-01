"""
市场数据服务 - 数据源管理器
按优先级从多个数据源获取数据
"""

import logging
from datetime import datetime
from typing import Optional

import pandas as pd

from ..vendor.base import VendorType, KType, FQType, MarketType
from ..vendor.tushare.provider import TushareProvider
from ..vendor.akshare.provider import AKShareProvider
from ..vendor.local.provider import LocalStorageProvider

logger = logging.getLogger(__name__)


class DataSourceManager:
    """
    数据源管理器
    按优先级从多个数据源获取数据
    """

    def __init__(self, config: dict):
        """
        初始化数据源管理器

        Args:
            config: 配置字典
                - tushare_token: Tushare Token
                - storage_type: 存储类型（hdf5/mysql）
                - hdf5_path: HDF5 文件路径
                - mysql_url: MySQL 连接字符串
                - vendor_priority: 数据源优先级列表
        """
        self.config = config
        self.providers = {}

        # 初始化数据源
        self._init_providers()

        # 设置数据源优先级
        self.priority = config.get(
            "vendor_priority",
            ["local", "tushare", "akshare"]
        )

    def _init_providers(self):
        """初始化数据提供者"""
        # 初始化本地存储提供者
        self.providers["local"] = LocalStorageProvider(
            storage_type=self.config.get("storage_type", "hdf5"),
            config=self.config,
        )

        # 初始化 Tushare 提供者
        tushare_token = self.config.get("tushare_token")
        if tushare_token:
            self.providers["tushare"] = TushareProvider(
                token=tushare_token,
                config=self.config,
            )
        else:
            logger.warning("未配置 Tushare Token，Tushare 提供者将不可用")

        # 初始化 AKShare 提供者
        self.providers["akshare"] = AKShareProvider(config=self.config)

    async def get_k_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        ktype: KType = KType.DAY,
        fq: FQType = FQType.BEFORE,
    ) -> pd.DataFrame:
        """
        按优先级获取K线数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            ktype: K线类型
            fq: 复权类型

        Returns:
            pd.DataFrame: K线数据
        """
        last_error = None

        # 按优先级尝试各数据源
        for vendor in self.priority:
            if vendor not in self.providers:
                continue

            provider = self.providers[vendor]
            try:
                logger.info(f"尝试从 {vendor} 获取K线数据: {symbol}")
                df = await provider.get_k_data(symbol, start_date, end_date, ktype, fq)

                if df is not None and not df.empty:
                    logger.info(f"从 {vendor} 成功获取 {len(df)} 条K线数据")
                    return df
                else:
                    logger.warning(f"{vendor} 返回空数据")

            except Exception as e:
                last_error = e
                logger.warning(f"从 {vendor} 获取K线数据失败: {e}")
                continue

        # 所有数据源都失败
        error_msg = f"所有数据源都无法获取K线数据: {symbol}"
        if last_error:
            error_msg += f", 最后错误: {last_error}"
        logger.error(error_msg)
        return pd.DataFrame()

    async def get_realtime_quote(self, symbol: str) -> Optional[dict]:
        """
        按优先级获取实时行情

        Args:
            symbol: 股票代码

        Returns:
            dict: 实时行情数据
        """
        # 本地存储不支持实时行情，跳过
        priority = [p for p in self.priority if p != "local"]

        for vendor in priority:
            if vendor not in self.providers:
                continue

            provider = self.providers[vendor]
            try:
                logger.info(f"尝试从 {vendor} 获取实时行情: {symbol}")
                quote = await provider.get_realtime_quote(symbol)

                if quote:
                    logger.info(f"从 {vendor} 成功获取实时行情")
                    return quote

            except Exception as e:
                logger.warning(f"从 {vendor} 获取实时行情失败: {e}")
                continue

        logger.error(f"所有数据源都无法获取实时行情: {symbol}")
        return None

    async def get_market_indexes(self) -> list:
        """
        按优先级获取市场指数

        Returns:
            list: 指数列表
        """
        # 本地存储不支持实时指数，跳过
        priority = [p for p in self.priority if p != "local"]

        for vendor in priority:
            if vendor not in self.providers:
                continue

            provider = self.providers[vendor]
            try:
                logger.info(f"尝试从 {vendor} 获取市场指数")
                indexes = await provider.get_market_indexes()

                if indexes:
                    logger.info(f"从 {vendor} 成功获取 {len(indexes)} 个指数")
                    return indexes

            except Exception as e:
                logger.warning(f"从 {vendor} 获取市场指数失败: {e}")
                continue

        logger.error("所有数据源都无法获取市场指数")
        return []

    async def search_stock(self, keyword: str) -> list:
        """
        按优先级搜索股票

        Args:
            keyword: 搜索关键词

        Returns:
            list: 股票列表
        """
        # 本地存储不支持搜索，跳过
        priority = [p for p in self.priority if p != "local"]

        for vendor in priority:
            if vendor not in self.providers:
                continue

            provider = self.providers[vendor]
            try:
                logger.info(f"尝试从 {vendor} 搜索股票: {keyword}")
                results = await provider.search_stock(keyword)

                if results:
                    logger.info(f"从 {vendor} 搜索到 {len(results)} 只股票")
                    return results

            except Exception as e:
                logger.warning(f"从 {vendor} 搜索股票失败: {e}")
                continue

        logger.error(f"所有数据源都无法搜索股票: {keyword}")
        return []

    async def get_stock_list(self, market: Optional[MarketType] = None) -> pd.DataFrame:
        """
        按优先级获取股票列表

        Args:
            market: 市场类型（可选）

        Returns:
            pd.DataFrame: 股票列表
        """
        # 本地存储不支持获取股票列表，跳过
        priority = [p for p in self.priority if p != "local"]

        for vendor in priority:
            if vendor not in self.providers:
                continue

            provider = self.providers[vendor]
            try:
                logger.info(f"尝试从 {vendor} 获取股票列表")
                df = await provider.get_stock_list(market)

                if df is not None and not df.empty:
                    logger.info(f"从 {vendor} 获取到 {len(df)} 只股票")
                    return df

            except Exception as e:
                logger.warning(f"从 {vendor} 获取股票列表失败: {e}")
                continue

        logger.error("所有数据源都无法获取股票列表")
        return pd.DataFrame()

    def get_provider_status(self) -> dict:
        """
        获取各数据源状态

        Returns:
            dict: 数据源状态
        """
        status = {}
        for name, provider in self.providers.items():
            status[name] = {
                "type": provider.vendor_type.value,
                "available": True,
            }
        return status
