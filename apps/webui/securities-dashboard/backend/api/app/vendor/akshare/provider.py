"""
AKShare 数据源提供者
参考 MyFunds apt/vendor/akshare/data.py
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import akshare as ak

from ..base import (
    BaseVendor,
    VendorType,
    KType,
    FQType,
    MarketType,
    KTYPE_MAP_AKSHARE,
)


class AKShareProvider(BaseVendor):
    """AKShare 数据源提供者"""

    def __init__(self, config: Optional[dict] = None):
        """
        初始化 AKShare 提供者

        Args:
            config: 额外配置
        """
        super().__init__(config)
        self.vendor_type = VendorType.AKSHARE
        self._loop = asyncio.get_event_loop()

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
        # 格式化代码为 AKShare 格式
        code = self._format_symbol_for_akshare(symbol)

        # 获取复权类型
        adjust = self._parse_fq_type(fq)

        # 获取K线数据
        if ktype in [KType.DAY, KType.WEEK, KType.MONTH]:
            period = "daily" if ktype == KType.DAY else ("weekly" if ktype == KType.WEEK else "monthly")
            df = await self._run_sync(
                ak.stock_zh_a_hist,
                symbol=code,
                period=period,
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust=adjust,
            )
        else:
            # 分钟级数据
            period = KTYPE_MAP_AKSHARE.get(ktype, "1")
            df = await self._run_sync(
                ak.stock_zh_a_hist_min_em,
                symbol=code,
                period=period,
                start_date=start_date.strftime("%Y%m%d %H:%M:%S"),
                end_date=end_date.strftime("%Y%m%d %H:%M:%S"),
                adjust=adjust,
            )

        if df is None or df.empty:
            return pd.DataFrame()

        # 标准化数据格式
        df = self._standardize_k_data(df, symbol)

        return df

    async def get_realtime_quote(self, symbol: str) -> dict:
        """
        获取实时行情报价

        Args:
            symbol: 股票代码

        Returns:
            dict: 实时行情数据
        """
        # 格式化代码
        code = self._format_symbol_for_akshare(symbol)

        # 获取实时行情
        df = await self._run_sync(ak.stock_zh_a_spot_em)

        if df is None or df.empty:
            raise ValueError("获取实时行情失败")

        # 查找对应股票
        row = df[df["代码"] == code]
        if row.empty:
            raise ValueError(f"未找到股票 {symbol} 的数据")

        row = row.iloc[0]
        price = self._parse_number(row.get("最新价"))
        close_prev = self._parse_number(row.get("昨收"))

        return {
            "symbol": symbol,
            "name": row.get("名称", ""),
            "price": price,
            "change": price - close_prev if close_prev else 0,
            "change_pct": self._parse_number(row.get("涨跌幅", 0)),
            "volume": self._parse_number(row.get("成交量", 0)),
            "amount": self._parse_number(row.get("成交额", 0)),
            "high": self._parse_number(row.get("最高", 0)),
            "low": self._parse_number(row.get("最低", 0)),
            "open": self._parse_number(row.get("今开", 0)),
            "close_prev": close_prev,
            "timestamp": datetime.now().isoformat(),
            "market": "SH" if symbol.endswith(".SH") else "SZ",
        }

    async def get_market_indexes(self) -> list:
        """
        获取市场主要指数

        Returns:
            list: 指数列表
        """
        # 获取实时指数行情
        df = await self._run_sync(ak.stock_zh_index_spot_em)

        if df is None or df.empty:
            return []

        # 主要指数代码映射
        index_codes = {
            "000001": "上证指数",
            "399001": "深证成指",
            "399006": "创业板指",
            "000300": "沪深300",
            "000016": "上证50",
            "399905": "中证500",
        }

        quotes = []
        for code, name in index_codes.items():
            row = df[df["代码"] == code]
            if not row.empty:
                row = row.iloc[0]
                price = self._parse_number(row.get("最新价"))
                close_prev = self._parse_number(row.get("昨收"))

                # 转换为带市场后缀的格式
                symbol = self._format_symbol_for_tushare(code)

                quotes.append(
                    {
                        "symbol": symbol,
                        "name": name,
                        "price": price,
                        "change": price - close_prev if close_prev else 0,
                        "change_pct": self._parse_number(row.get("涨跌幅", 0)),
                        "volume": self._parse_number(row.get("成交量", 0)),
                        "amount": self._parse_number(row.get("成交额", 0)),
                        "high": self._parse_number(row.get("最高", 0)),
                        "low": self._parse_number(row.get("最低", 0)),
                        "open": self._parse_number(row.get("今开", 0)),
                        "close_prev": close_prev,
                        "timestamp": datetime.now().isoformat(),
                        "market": "SH" if code.startswith("000") or code.startswith("0006") else "SZ",
                    }
                )

        return quotes

    async def search_stock(self, keyword: str) -> list:
        """
        搜索股票

        Args:
            keyword: 搜索关键词（代码或名称）

        Returns:
            list: 股票列表
        """
        # 获取所有A股列表
        df = await self._run_sync(ak.stock_zh_a_spot_em)

        if df is None or df.empty:
            return []

        # 搜索匹配
        results = []
        for _, row in df.iterrows():
            code = row.get("代码", "")
            name = row.get("名称", "")

            if keyword in code or keyword in name:
                symbol = self._format_symbol_for_tushare(code)
                results.append(
                    {
                        "code": symbol,
                        "name": name,
                        "market": "SH" if code.startswith("6") else "SZ",
                    }
                )

        return results[:50]  # 限制返回50条结果

    async def get_stock_list(self, market: Optional[MarketType] = None) -> pd.DataFrame:
        """
        获取股票列表

        Args:
            market: 市场类型（可选）

        Returns:
            pd.DataFrame: 股票列表
        """
        # 获取A股列表
        df = await self._run_sync(ak.stock_zh_a_spot_em)

        if df is None or df.empty:
            return pd.DataFrame()

        # 标准化列名
        df = df.rename(columns={"代码": "symbol", "名称": "name"})

        # 添加市场后缀
        df["symbol"] = df["symbol"].apply(
            lambda x: f"{x}.SH" if str(x).startswith("6") else f"{x}.SZ"
        )

        # 按市场筛选
        if market == MarketType.SH:
            df = df[df["symbol"].str.endswith(".SH")]
        elif market == MarketType.SZ:
            df = df[df["symbol"].str.endswith(".SZ")]

        return df[["symbol", "name"]]

    def _parse_number(self, value) -> float:
        """解析数字（处理带逗号的数字）"""
        if value is None or value == "-":
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # 移除逗号
            value = value.replace(",", "")
            try:
                return float(value)
            except ValueError:
                return 0.0
        return 0.0
