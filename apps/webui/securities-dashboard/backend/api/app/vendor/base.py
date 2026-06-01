"""
数据源提供者统一接口基类
参考 MyFunds apt/qsp_universal/base.py
"""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Union

import pandas as pd


class VendorType(str, Enum):
    """数据源类型"""
    TUSHARE = "tushare"
    TUSHARE_PRO = "tushare_pro"
    AKSHARE = "akshare"
    LOCAL = "local"


class FQType(int, Enum):
    """复权类型"""
    NONE = 0      # 不复权
    BEFORE = 1    # 前复权
    AFTER = 2     # 后复权
    DYNAMIC = 3   # 动态复权


class KType(str, Enum):
    """K线类型"""
    MIN = "1min"
    MIN5 = "5min"
    MIN15 = "15min"
    MIN30 = "30min"
    MIN60 = "60min"
    DAY = "daily"
    WEEK = "weekly"
    MONTH = "monthly"


class MarketType(str, Enum):
    """市场类型"""
    SH = "SH"    # 上海
    SZ = "SZ"    # 深圳
    BJ = "BJ"    # 北京


# K线周期映射（用于 AKShare）
KTYPE_MAP_AKSHARE = {
    KType.MIN: "1",
    KType.MIN5: "5",
    KType.MIN15: "15",
    KType.MIN30: "30",
    KType.MIN60: "60",
    KType.DAY: "101",
    KType.WEEK: "102",
    KType.MONTH: "103",
}

# K线周期映射（用于 Tushare）
KTYPE_MAP_TUSHARE = {
    KType.MIN: "1min",
    KType.MIN5: "5min",
    KType.MIN15: "15min",
    KType.MIN30: "30min",
    KType.MIN60: "60min",
    KType.DAY: "D",
    KType.WEEK: "W",
    KType.MONTH: "M",
}


class BaseVendor(ABC):
    """
    数据源提供者基类
    定义统一的数据获取接口
    """

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.vendor_type = VendorType.LOCAL

    @abstractmethod
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
            symbol: 股票代码（如 "000001.SZ"）
            start_date: 开始日期
            end_date: 结束日期
            ktype: K线类型
            fq: 复权类型

        Returns:
            pd.DataFrame: 包含以下列的数据框
                - symbol: 股票代码
                - date: 日期
                - open: 开盘价
                - high: 最高价
                - low: 最低价
                - close: 收盘价
                - volume: 成交量
                - amount: 成交额
        """
        pass

    @abstractmethod
    async def get_realtime_quote(self, symbol: str) -> dict:
        """
        获取实时行情报价

        Args:
            symbol: 股票代码

        Returns:
            dict: 实时行情数据
        """
        pass

    @abstractmethod
    async def get_market_indexes(self) -> list:
        """
        获取市场主要指数

        Returns:
            list: 指数列表
        """
        pass

    @abstractmethod
    async def search_stock(self, keyword: str) -> list:
        """
        搜索股票

        Args:
            keyword: 搜索关键词（代码或名称）

        Returns:
            list: 股票列表
        """
        pass

    @abstractmethod
    async def get_stock_list(self, market: Optional[MarketType] = None) -> pd.DataFrame:
        """
        获取股票列表

        Args:
            market: 市场类型（可选）

        Returns:
            pd.DataFrame: 股票列表
        """
        pass

    def _standardize_k_data(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        标准化K线数据格式

        Args:
            df: 原始数据
            symbol: 股票代码

        Returns:
            pd.DataFrame: 标准化后的数据
        """
        # 确保必要的列存在
        required_columns = ["date", "open", "high", "low", "close", "volume"]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"缺少必要的列: {col}")

        # 重命名列以统一格式
        column_mapping = {
            "datetime": "date",
            "time": "date",
            "trade_date": "date",
            "ts_code": "symbol",
            "code": "symbol",
            "vol": "volume",
            "amt": "amount",
            "money": "amount",
        }
        df = df.rename(columns=column_mapping)

        # 添加 symbol 列
        if "symbol" not in df.columns:
            df["symbol"] = symbol

        # 添加 amount 列（如果不存在）
        if "amount" not in df.columns:
            df["amount"] = 0

        # 确保日期格式正确
        if df["date"].dtype == "object":
            df["date"] = pd.to_datetime(df["date"])

        # 按日期排序
        df = df.sort_values("date").reset_index(drop=True)

        return df[["symbol", "date", "open", "high", "low", "close", "volume", "amount"]]

    def _format_symbol_for_tushare(self, symbol: str) -> str:
        """
        格式化股票代码为 Tushare 格式

        Args:
            symbol: 股票代码（如 "000001" 或 "000001.SZ"）

        Returns:
            str: Tushare 格式的代码（如 "000001.SZ"）
        """
        if "." in symbol:
            return symbol

        # 根据代码前缀判断市场
        if symbol.startswith("6"):
            return f"{symbol}.SH"
        elif symbol.startswith("0") or symbol.startswith("3"):
            return f"{symbol}.SZ"
        elif symbol.startswith("8") or symbol.startswith("4"):
            return f"{symbol}.BJ"
        else:
            return symbol

    def _format_symbol_for_akshare(self, symbol: str) -> str:
        """
        格式化股票代码为 AKShare 格式

        Args:
            symbol: 股票代码（如 "000001.SZ"）

        Returns:
            str: AKShare 格式的代码（如 "000001"）
        """
        if "." not in symbol:
            return symbol
        return symbol.split(".")[0]

    def _parse_fq_type(self, fq: FQType) -> str:
        """
        解析复权类型

        Args:
            fq: 复权类型枚举

        Returns:
            str: 复权类型字符串
        """
        if fq == FQType.NONE:
            return ""
        elif fq == FQType.BEFORE:
            return "qfq"
        elif fq == FQType.AFTER:
            return "hfq"
        elif fq == FQType.DYNAMIC:
            return ""
        return ""
