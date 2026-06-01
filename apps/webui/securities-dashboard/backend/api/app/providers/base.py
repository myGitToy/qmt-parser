"""Base market data provider interface"""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal

from app.models.market import Bar, Quote


class MarketDataProvider(ABC):
    """市场数据提供者抽象基类"""

    @abstractmethod
    async def get_realtime_quote(self, symbol: str) -> Quote:
        """
        获取实时行情报价

        Args:
            symbol: 股票代码，如 "000001.SZ" 或 "600000.SH"

        Returns:
            Quote: 实时行情数据
        """
        pass

    @abstractmethod
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
            timeframe: 周期 (1min/5min/15min/30min/60min/daily/weekly/monthly)
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            list[Bar]: K线数据列表
        """
        pass

    @abstractmethod
    async def get_market_indexes(self) -> list[Quote]:
        """
        获取市场主要指数

        Returns:
            list[Quote]: 指数列表
        """
        pass

    @abstractmethod
    async def search_stocks(self, keyword: str) -> list[dict]:
        """
        搜索股票

        Args:
            keyword: 搜索关键词（代码或名称）

        Returns:
            list[dict]: 股票列表，包含 code 和 name 字段
        """
        pass

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 提供者是否可用
        """
        try:
            # 尝试获取一个简单的数据来验证连接
            await self.get_market_indexes()
            return True
        except Exception:
            return False
