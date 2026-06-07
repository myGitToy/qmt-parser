"""
xtquant数据解析器包

提供tick数据、分钟K线数据、日线K线数据、财务数据、板块成分股和除权数据的解析功能
"""

from .tick import parse_ticks
from .min import parse_1min_kline
from .day import parse_daily_kline
from .finance import parse_finance
from .sector import parse_sector_file
from .dividend import list_dividend_codes, parse_dividend_records

__all__ = [
    "parse_ticks",
    "parse_1min_kline",
    "parse_daily_kline",
    "parse_finance",
    "parse_sector_file",
    "list_dividend_codes",
    "parse_dividend_records",
]
__version__ = "1.2.0"
