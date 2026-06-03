"""AKShare market data provider (fallback)"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal

import akshare as ak
from app.models.market import Bar, Quote
from app.providers.base import MarketDataProvider


class AKShareProvider(MarketDataProvider):
    """AKShare 数据提供者（备用）"""

    def __init__(self):
        """初始化 AKShare 提供者"""
        self._loop = asyncio.get_event_loop()

    def _run_sync(self, func, *args, **kwargs):
        """在异步上下文中运行同步函数"""
        return self._loop.run_in_executor(None, func, *args, **kwargs)

    async def get_realtime_quote(self, symbol: str) -> Quote:
        """
        获取实时行情报价

        Args:
            symbol: 股票代码，格式 "000001"（不带后缀）

        Returns:
            Quote: 实时行情数据
        """
        # 转换代码格式
        code = self._convert_symbol_format(symbol, reverse=True)

        # 获取实时行情
        df = await self._run_sync(
            ak.stock_zh_a_spot_em,
        )

        # 查找对应股票
        row = df[df["代码"] == code]
        if row.empty:
            raise ValueError(f"未找到股票 {symbol} 的数据")

        row = row.iloc[0]
        price = Decimal(str(row["最新价"]))
        close_prev = Decimal(str(row["昨收"]))

        return Quote(
            symbol=symbol,
            name=row["名称"],
            price=price,
            change=price - close_prev,
            change_pct=Decimal(str(row["涨跌幅"])),
            volume=int(str(row["成交量"]).replace(",", "")) if row["成交量"] else 0,
            amount=Decimal(str(row["成交额"]).replace(",", "")) if row["成交额"] else Decimal("0"),
            high=Decimal(str(row["最高"])) if row["最高"] else None,
            low=Decimal(str(row["最低"])) if row["最低"] else None,
            open_price=Decimal(str(row["今开"])) if row["今开"] else None,
            close_prev=close_prev,
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
        # 转换代码格式
        code = self._convert_symbol_format(symbol, reverse=True)

        # AKShare 使用不同的接口获取不同周期的数据
        if timeframe in ["daily"]:
            df = await self._run_sync(
                ak.stock_zh_a_hist,
                symbol=code,
                period="daily",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust="qfq",  # 前复权
            )
        elif timeframe in ["weekly"]:
            df = await self._run_sync(
                ak.stock_zh_a_hist,
                symbol=code,
                period="weekly",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust="qfq",
            )
        elif timeframe in ["monthly"]:
            df = await self._run_sync(
                ak.stock_zh_a_hist,
                symbol=code,
                period="monthly",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust="qfq",
            )
        else:
            # 分钟级数据
            period_map = {
                "1min": "1",
                "5min": "5",
                "15min": "15",
                "30min": "30",
                "60min": "60",
            }
            period = period_map.get(timeframe, "1")
            df = await self._run_sync(
                ak.stock_zh_a_hist_min_em,
                symbol=code,
                period=period,
                start_date=start_date.strftime("%Y%m%d %H:%M:%S"),
                end_date=end_date.strftime("%Y%m%d %H:%M:%S"),
                adjust="qfq",
            )

        bars = []
        for _, row in df.iterrows():
            # 解析日期
            if timeframe in ["daily", "weekly", "monthly"]:
                dt = datetime.strptime(row["日期"], "%Y-%m-%d")
            else:
                dt = datetime.strptime(row["时间"], "%Y-%m-%d %H:%M:%S")

            bars.append(
                Bar(
                    symbol=symbol,
                    timeframe=timeframe,
                    datetime=dt,
                    open_price=Decimal(str(row["开盘"])),
                    high=Decimal(str(row["最高"])),
                    low=Decimal(str(row["最低"])),
                    close=Decimal(str(row["收盘"])),
                    volume=int(str(row["成交量"]).replace(",", "")),
                    amount=Decimal(str(row["成交额"]).replace(",", "")) if "成交额" in row else None,
                )
            )

        return bars

    async def get_market_indexes(self) -> list[Quote]:
        """
        获取市场主要指数

        Returns:
            list[Quote]: 指数列表
        """
        # 获取实时指数行情
        df = await self._run_sync(ak.stock_zh_index_spot_em)

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
                price = Decimal(str(row["最新价"]))
                close_prev = Decimal(str(row["昨收"]))

                # 转换为带市场后缀的格式
                symbol = self._convert_symbol_format(code)

                quotes.append(
                    Quote(
                        symbol=symbol,
                        name=name,
                        price=price,
                        change=price - close_prev,
                        change_pct=Decimal(str(row["涨跌幅"])),
                        volume=int(str(row["成交量"]).replace(",", "")) if row["成交量"] else 0,
                        amount=Decimal(str(row["成交额"]).replace(",", "")) if row["成交额"] else Decimal("0"),
                        high=Decimal(str(row["最高"])) if row["最高"] else None,
                        low=Decimal(str(row["最低"])) if row["最低"] else None,
                        open_price=Decimal(str(row["今开"])) if row["今开"] else None,
                        close_prev=close_prev,
                        timestamp=datetime.now(),
                        market="SH" if code.startswith("000") or code.startswith("0006") else "SZ",
                    )
                )

        return quotes

    async def search_stocks(self, keyword: str) -> list[dict]:
        """
        搜索股票

        Args:
            keyword: 搜索关键词（代码或名称）

        Returns:
            list[dict]: 股票列表，包含 code 和 name 字段
        """
        # 获取所有A股列表
        df = await self._run_sync(ak.stock_zh_a_spot_em)

        # 搜索匹配
        results = []
        for _, row in df.iterrows():
            code = row["代码"]
            name = row["名称"]

            if keyword in code or keyword in name:
                results.append(
                    {
                        "code": self._convert_symbol_format(code),
                        "name": name,
                        "market": "SH" if code.startswith("6") else "SZ",
                    }
                )

        return results[:50]  # 限制返回50条结果

    def _convert_symbol_format(self, symbol: str, reverse: bool = False) -> str:
        """
        转换股票代码格式

        Args:
            symbol: 股票代码
            reverse: 是否反向转换（从Tushare格式到AKShare格式）

        Returns:
            str: 转换后的代码
        """
        if reverse:
            # Tushare格式 -> AKShare格式
            # 000001.SZ -> 000001
            # 600000.SH -> 600000
            return symbol.split(".")[0]
        else:
            # AKShare格式 -> Tushare格式
            # 000001 -> 000001.SZ
            # 600000 -> 600000.SH
            if symbol.startswith("6"):
                return f"{symbol}.SH"
            elif symbol.startswith("0") or symbol.startswith("3"):
                return f"{symbol}.SZ"
            else:
                # 指数
                if symbol.startswith("000") or symbol.startswith("0006"):
                    return f"{symbol}.SH"
                else:
                    return f"{symbol}.SZ"
