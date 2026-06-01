"""
Tushare 数据源提供者
参考 MyFunds apt/vendor/tspro/tspro.py
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import tushare as ts

from ..base import (
    BaseVendor,
    VendorType,
    KType,
    FQType,
    MarketType,
    KTYPE_MAP_TUSHARE,
)


class TushareProvider(BaseVendor):
    """Tushare 数据源提供者"""

    def __init__(self, token: str, config: Optional[dict] = None):
        """
        初始化 Tushare 提供者

        Args:
            token: Tushare Pro API Token
            config: 额外配置
        """
        super().__init__(config)
        self.token = token
        self.pro = ts.pro_api(token)
        self.vendor_type = VendorType.TUSHARE_PRO
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
        # 格式化代码
        symbol = self._format_symbol_for_tushare(symbol)

        # 格式化日期
        start = start_date.strftime("%Y%m%d")
        end = end_date.strftime("%Y%m%d")

        # 获取K线数据
        if ktype in [KType.DAY, KType.WEEK, KType.MONTH]:
            df = await self._run_sync(
                self.pro.daily,
                ts_code=symbol,
                start_date=start,
                end_date=end,
            )
        elif ktype == KType.MIN:
            # 1分钟数据需要高级权限
            raise NotImplementedError(f"Tushare Pro 暂不支持 {ktype.value} 级别数据，需要高级权限")
        else:
            raise NotImplementedError(f"Tushare Pro 暂不支持 {ktype.value} 级别数据")

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
        symbol = self._format_symbol_for_tushare(symbol)

        # 获取最新交易日数据
        today = datetime.now().strftime("%Y%m%d")
        df = await self._run_sync(
            self.pro.daily,
            ts_code=symbol,
            trade_date=today,
        )

        if df is None or df.empty:
            # 尝试获取最近一个交易日
            df = await self._run_sync(
                self.pro.daily,
                ts_code=symbol,
                limit=1,
            )

        if df is None or df.empty:
            raise ValueError(f"未找到股票 {symbol} 的数据")

        row = df.iloc[0]
        close_prev = row.get("pre_close", row.get("close", 0))
        current = row.get("close", 0)

        return {
            "symbol": row.get("ts_code", symbol),
            "name": "",  # 需要另外获取
            "price": float(current),
            "change": float(current - close_prev),
            "change_pct": float((current / close_prev - 1) * 100) if close_prev > 0 else 0,
            "volume": int(row.get("vol", 0)),
            "amount": float(row.get("amount", 0)) * 1000,  # Tushare 的单位是千元
            "high": float(row.get("high", 0)),
            "low": float(row.get("low", 0)),
            "open": float(row.get("open", 0)),
            "close_prev": float(close_prev),
            "timestamp": datetime.now().isoformat(),
            "market": "SH" if symbol.endswith(".SH") else "SZ",
        }

    async def get_market_indexes(self) -> list:
        """
        获取市场主要指数

        Returns:
            list: 指数列表
        """
        # 主要指数代码
        index_codes = [
            "000001.SH",  # 上证指数
            "399001.SZ",  # 深证成指
            "399006.SZ",  # 创业板指
            "000300.SH",  # 沪深300
            "000016.SH",  # 上证50
            "399905.SZ",  # 中证500
        ]

        quotes = []
        today = datetime.now().strftime("%Y%m%d")

        for code in index_codes:
            try:
                df = await self._run_sync(
                    self.pro.index_daily,
                    ts_code=code,
                    trade_date=today,
                )

                if df is None or df.empty:
                    df = await self._run_sync(
                        self.pro.index_daily,
                        ts_code=code,
                        limit=1,
                    )

                if df is not None and not df.empty:
                    row = df.iloc[0]
                    close_prev = row.get("pre_close", row.get("close", 0))
                    current = row.get("close", 0)

                    quotes.append(
                        {
                            "symbol": row.get("ts_code", code),
                            "name": self._get_index_name(row.get("ts_code", code)),
                            "price": float(current),
                            "change": float(current - close_prev),
                            "change_pct": float((current / close_prev - 1) * 100) if close_prev > 0 else 0,
                            "volume": int(row.get("vol", 0)) if "vol" in row else None,
                            "amount": float(row.get("amount", 0)) * 1000 if "amount" in row else None,
                            "high": float(row.get("high", 0)) if "high" in row else None,
                            "low": float(row.get("low", 0)) if "low" in row else None,
                            "open": float(row.get("open", 0)) if "open" in row else None,
                            "close_prev": float(close_prev),
                            "timestamp": datetime.now().isoformat(),
                            "market": "SH" if code.endswith(".SH") else "SZ",
                        }
                    )
            except Exception as e:
                print(f"获取指数 {code} 数据失败: {e}")
                continue

        return quotes

    async def search_stock(self, keyword: str) -> list:
        """
        搜索股票

        Args:
            keyword: 搜索关键词（代码或名称）

        Returns:
            list: 股票列表
        """
        # Tushare 股票列表接口
        df = await self._run_sync(
            self.pro.stock_basic,
            ts_code=keyword,
            name=keyword,
            list_status="L",  # 仅上市股票
        )

        if df is None or df.empty:
            # 尝试模糊搜索
            df = await self._run_sync(
                self.pro.stock_basic,
                name=keyword,
                list_status="L",
            )

        results = []
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                results.append(
                    {
                        "code": row.get("ts_code", ""),
                        "name": row.get("name", ""),
                        "market": "SH" if row.get("ts_code", "").endswith(".SH") else "SZ",
                    }
                )

        return results

    async def get_stock_list(self, market: Optional[MarketType] = None) -> pd.DataFrame:
        """
        获取股票列表

        Args:
            market: 市场类型（可选）

        Returns:
            pd.DataFrame: 股票列表
        """
        df = await self._run_sync(
            self.pro.stock_basic,
            list_status="L",  # 仅上市股票
        )

        if df is None or df.empty:
            return pd.DataFrame()

        # 标准化列名
        df = df.rename(columns={"ts_code": "symbol", "name": "name"})

        # 按市场筛选
        if market == MarketType.SH:
            df = df[df["symbol"].str.endswith(".SH")]
        elif market == MarketType.SZ:
            df = df[df["symbol"].str.endswith(".SZ")]
        elif market == MarketType.BJ:
            df = df[df["symbol"].str.endswith(".BJ")]

        return df[["symbol", "name", "market", "industry"]]

    def _get_index_name(self, code: str) -> str:
        """获取指数名称"""
        names = {
            "000001.SH": "上证指数",
            "399001.SZ": "深证成指",
            "399006.SZ": "创业板指",
            "000300.SH": "沪深300",
            "000016.SH": "上证50",
            "399905.SZ": "中证500",
            "000688.SH": "科创50",
            "399671.SZ": "深证50",
        }
        return names.get(code, code)
