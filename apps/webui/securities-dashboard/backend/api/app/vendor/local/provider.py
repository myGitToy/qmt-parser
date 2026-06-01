"""
本地存储数据源提供者
参考 MyFunds apt/os/hdf5.py
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from ..base import (
    BaseVendor,
    VendorType,
    KType,
    FQType,
    MarketType,
)


class LocalStorageProvider(BaseVendor):
    """本地存储数据源提供者（HDF5/MySQL）"""

    def __init__(
        self,
        storage_type: str = "hdf5",
        config: Optional[dict] = None,
    ):
        """
        初始化本地存储提供者

        Args:
            storage_type: 存储类型（hdf5 或 mysql）
            config: 配置信息
        """
        super().__init__(config)
        self.storage_type = storage_type
        self.vendor_type = VendorType.LOCAL
        self._loop = asyncio.get_event_loop()

        # 获取配置
        self.hdf5_path = config.get("hdf5_path", "C:/Data/hdf5") if config else "C:/Data/hdf5"
        self.mysql_url = config.get("mysql_url") if config else None

    def _run_sync(self, func, *args, **kwargs):
        """在异步上下文中运行同步函数"""
        return self._loop.run_in_executor(None, func, *args, **kwargs)

    async def get_k_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        ktype: KType = KType.DAY,
        fq: FQType = FQType.BEFORE,
    ) -> pd.DataFrame:
        """
        获取K线数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            ktype: K线类型
            fq: 复权类型

        Returns:
            pd.DataFrame: K线数据
        """
        if self.storage_type == "hdf5":
            return await self._get_k_data_from_hdf5(symbol, start_date, end_date, ktype)
        elif self.storage_type == "mysql":
            return await self._get_k_data_from_mysql(symbol, start_date, end_date, ktype)
        else:
            return pd.DataFrame()

    async def _get_k_data_from_hdf5(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        ktype: KType,
    ) -> pd.DataFrame:
        """从 HDF5 文件读取K线数据"""
        try:
            # 格式化代码（移除市场后缀）
            code = self._format_symbol_for_akshare(symbol)

            # 根据K线类型确定key
            key = f"{ktype.value}"

            # 文件路径
            file_path = Path(self.hdf5_path) / f"{code}.h5"

            if not file_path.exists():
                return pd.DataFrame()

            # 读取数据
            where_clause = f"date >= '{start_date.strftime('%Y-%m-%d')}' & date <= '{end_date.strftime('%Y-%m-%d')}'"
            df = await self._run_sync(
                pd.read_hdf,
                str(file_path),
                key=key,
                where=where_clause,
            )

            if df is None or df.empty:
                return pd.DataFrame()

            # 标准化数据格式
            df = self._standardize_k_data(df, symbol)

            return df

        except Exception as e:
            print(f"从 HDF5 读取数据失败: {e}")
            return pd.DataFrame()

    async def _get_k_data_from_mysql(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        ktype: KType,
    ) -> pd.DataFrame:
        """从 MySQL 数据库读取K线数据"""
        try:
            from sqlalchemy import create_engine, text

            if not self.mysql_url:
                return pd.DataFrame()

            engine = create_engine(self.mysql_url)

            # 构建SQL查询
            code = self._format_symbol_for_akshare(symbol)
            table_name = f"stock_{ktype.value}"

            query = f"""
                SELECT * FROM {table_name}
                WHERE symbol = '{symbol}'
                AND date >= '{start_date.strftime("%Y-%m-%d")}'
                AND date <= '{end_date.strftime("%Y-%m-%d")}'
                ORDER BY date
            """

            df = await self._run_sync(pd.read_sql, query, engine)

            if df is None or df.empty:
                return pd.DataFrame()

            # 标准化数据格式
            df = self._standardize_k_data(df, symbol)

            return df

        except Exception as e:
            print(f"从 MySQL 读取数据失败: {e}")
            return pd.DataFrame()

    async def get_realtime_quote(self, symbol: str) -> dict:
        """
        获取实时行情报价

        注意：本地存储不支持实时行情，返回空数据

        Args:
            symbol: 股票代码

        Returns:
            dict: 空数据
        """
        # 本地存储不支持实时行情
        return {}

    async def get_market_indexes(self) -> list:
        """
        获取市场主要指数

        注意：本地存储不支持实时指数，返回空列表

        Returns:
            list: 空列表
        """
        # 本地存储不支持实时指数
        return []

    async def search_stock(self, keyword: str) -> list:
        """
        搜索股票

        注意：本地存储不支持搜索，返回空列表

        Args:
            keyword: 搜索关键词

        Returns:
            list: 空列表
        """
        # 本地存储不支持搜索
        return []

    async def get_stock_list(self, market: Optional[MarketType] = None) -> pd.DataFrame:
        """
        获取股票列表

        注意：本地存储不支持获取股票列表，返回空数据框

        Args:
            market: 市场类型（可选）

        Returns:
            pd.DataFrame: 空数据框
        """
        # 本地存储不支持获取股票列表
        return pd.DataFrame()

    async def save_k_data_to_hdf5(
        self,
        df: pd.DataFrame,
        symbol: str,
        ktype: KType,
    ) -> bool:
        """
        保存K线数据到 HDF5 文件

        Args:
            df: K线数据
            symbol: 股票代码
            ktype: K线类型

        Returns:
            bool: 是否保存成功
        """
        try:
            # 格式化代码
            code = self._format_symbol_for_akshare(symbol)

            # 文件路径
            file_path = Path(self.hdf5_path) / f"{code}.h5"

            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # 根据K线类型确定key
            key = f"{ktype.value}"

            # 保存数据（追加模式）
            await self._run_sync(
                df.to_hdf,
                str(file_path),
                key=key,
                mode="a",
                format="table",
            )

            return True

        except Exception as e:
            print(f"保存数据到 HDF5 失败: {e}")
            return False

    def check_hdf5_file_exists(self, symbol: str, ktype: KType) -> bool:
        """
        检查 HDF5 文件是否存在

        Args:
            symbol: 股票代码
            ktype: K线类型

        Returns:
            bool: 文件是否存在
        """
        code = self._format_symbol_for_akshare(symbol)
        file_path = Path(self.hdf5_path) / f"{code}.h5"
        return file_path.exists()
