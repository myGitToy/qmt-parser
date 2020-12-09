from jqdatasdk import *
import pandas as pd
import datetime
import sqlalchemy
from apt.vendor.jqdata.jqdata import jqdata as jqdata
from apt.vendor.jqdata.ETF import ETF as ETF

"""
聚宽数据每日更新
日线分时线：
日行情	：盘中实时更新（每3s刷新一次）
分钟行情：盘中实时更新（每3s刷新一次）盘后24:00更新
融资融券	2010至今	下一个交易日10点之前更新
资金流向	2010至今	盘后20:00更新
龙虎榜数据	2005至今	盘后18:00更新
沪深市场每日成交概况	2005年至今	交易日20:30-24:00更新
沪股通，深股通和港股通(市场通数据）	上市至今	交易日20:30-06:30更新
分级基金数据	2005至今	8:00更新
日行情	2005至今	盘中实时更新（每3s刷新一次）
分钟行情	2005至今	盘前9:00更新 盘中实时更新（每3s刷新一次）盘后24:00更新
"""

start = datetime.datetime(2020,12,1)
end = datetime.datetime(2020,11,28,16)


etf = ETF()
etf.update_fund_share_daily(start_date = start)


