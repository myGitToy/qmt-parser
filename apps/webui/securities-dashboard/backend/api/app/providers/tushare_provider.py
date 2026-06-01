"""Tushare Pro market data provider"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal

import tushare as ts
from app.models.market import Bar, Quote
from app.providers.base import MarketDataProvider


class TushareProvider(MarketDataProvider):
    """Tushare Pro 数据提供者"""

    def __init__(self, token: str):
        """
        初始化 Tushare Pro 提供者

        Args:
            token: Tushare Pro API token
        """
        self.token = token
        self.pro = ts.pro_api(token)
        self._loop = asyncio.get_event_loop()

    def _run_sync(self, func, *args, **kwargs):
        """在异步上下文中运行同步函数"""
        return self._loop.run_in_executor(None, func, *args, **kwargs)

    async def get_realtime_quote(self, symbol: str) -> Quote:
        """
        获取实时行情报价

        Args:
            symbol: 股票代码，格式 "000001.SZ" 或 "600000.SH"

        Returns:
            Quote: 实时行情数据
        """
        # Tushare 使用 daily 接口获取最新行情
        # 注意：Tushare Pro 的实时接口需要积分权限
        # 这里使用 daily 接口模拟
        today = datetime.now().strftime("%Y%m%d")
        df = await self._run_sync(
            self.pro.daily,
            ts_code=symbol,
            trade_date=today,
        )

        if df.empty:
            # 尝试获取最近一个交易日
            df = await self._run_sync(
                self.pro.daily,
                ts_code=symbol,
                limit=1,
            )

        if df.empty:
            raise ValueError(f"未找到股票 {symbol} 的数据")

        row = df.iloc[0]
        close_prev = row["pre_close"]

        return Quote(
            symbol=row["ts_code"],
            name="",  # 需要另外获取名称
            price=Decimal(str(row["close"])),
            change=Decimal(str(row["close"])) - Decimal(str(close_prev)),
            change_pct=Decimal(str((row["close"] / close_prev - 1) * 100)),
            volume=int(row["vol"]),
            amount=Decimal(str(row["amount"])) * 1000,  # Tushare 的单位是千元
            high=Decimal(str(row["high"])),
            low=Decimal(str(row["low"])),
            open=Decimal(str(row["open"])),
            close_prev=Decimal(str(close_prev)),
            timestamp=datetime.now(),
            market="SH" if symbol.endswith(".SH") else "SZ",
        )

    async def get_historical_bars(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[Bar]:
        """
        获取历史K线数据

        Args:
            symbol: 股票代码
            timeframe: 周期
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            list[Bar]: K线数据列表
        """
        # Tushare 主要支持日线数据
        start = start_date.strftime("%Y%m%d")
        end = end_date.strftime("%Y%m%d")

        # 根据周期选择接口
        if timeframe in ["daily", "weekly", "monthly"]:
            df = await self._run_sync(
                self.pro.daily,
                ts_code=symbol,
                start_date=start,
                end_date=end,
            )
        else:
            # 分钟级数据需要高级权限
            raise NotImplementedError(f"Tushare Pro 暂不支持 {timeframe} 级别数据，需要高级权限")

        bars = []
        for _, row in df.iterrows():
            bars.append(
                Bar(
                    symbol=row["ts_code"],
                    timeframe=timeframe,
                    datetime=datetime.strptime(row["trade_date"], "%Y%m%d"),
                    open=Decimal(str(row["open"])),
                    high=Decimal(str(row["high"])),
                    low=Decimal(str(row["low"])),
                    close=Decimal(str(row["close"])),
                    volume=int(row["vol"]),
                    amount=Decimal(str(row["amount"])) * 1000,
                )
            )

        return bars

    async def get_market_indexes(self) -> list[Quote]:
        """
        获取市场主要指数

        Returns:
            list[Quote]: 指数列表
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

                if df.empty:
                    df = await self._run_sync(
                        self.pro.index_daily,
                        ts_code=code,
                        limit=1,
                    )

                if not df.empty:
                    row = df.iloc[0]
                    close_prev = row["pre_close"]

                    quotes.append(
                        Quote(
                            symbol=row["ts_code"],
                            name=self._get_index_name(row["ts_code"]),
                            price=Decimal(str(row["close"])),
                            change=Decimal(str(row["close"])) - Decimal(str(close_prev)),
                            change_pct=Decimal(str((row["close"] / close_prev - 1) * 100)),
                            volume=int(row["vol"]) if "vol" in row else None,
                            amount=Decimal(str(row["amount"])) * 1000 if "amount" in row else None,
                            high=Decimal(str(row["high"])) if "high" in row else None,
                            low=Decimal(str(row["low"])) if "low" in row else None,
                            open=Decimal(str(row["open"])) if "open" in row else None,
                            close_prev=Decimal(str(close_prev)),
                            timestamp=datetime.now(),
                            market="SH" if code.endswith(".SH") else "SZ",
                        )
                    )
            except Exception as e:
                print(f"获取指数 {code} 数据失败: {e}")
                continue

        return quotes

    async def search_stocks(self, keyword: str) -> list[dict]:
        """
        搜索股票

        Args:
            keyword: 搜索关键词（代码或名称）

        Returns:
            list[dict]: 股票列表，包含 ts_code 和 name 字段
        """
        # Tushare 股票列表接口
        df = await self._run_sync(self.pro.stock_basic, ts_code=keyword, name=keyword)

        if df.empty:
            # 模糊搜索
            df = await self._run_sync(
                self.pro.stock_basic,
                name=keyword,
                list_status="L",  # 仅上市股票
            )

        results = []
        for _, row in df.iterrows():
            results.append(
                {
                    "code": row["ts_code"],
                    "name": row["name"],
                    "market": "SH" if row["ts_code"].endswith(".SH") else "SZ",
                }
            )

        return results

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
