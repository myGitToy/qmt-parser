import numpy as np
import pandas as pd
import tushare as ts
import sqlalchemy
import datetime
from jqdatasdk import *
from apt.vendor.jqdata.base import base as base
from apt.vendor.jqdata.ETF import ETF as ETF
from apt.vendor.jqdata.money_flow import money_flow as money_flow

"""
此模块用于进行ETF 资金流向表 大宗交易 北向资金 valudation表的日常更新
开始日期不需要频繁更新，每半年或每季度重置即可
"""
######初始化######
start = datetime.datetime(2021,1,1)
end = datetime.datetime.now()
count_start = get_query_count()
print(f"开始更新 数据条目剩余{count_start}")

######ETF更新模块######
etf = ETF()
etf.update_fund_share_daily(start_date = start , end_date = end)

######资金流向更新模块######
money = money_flow()
money.daily_update(start_date = start , end_date = end)
#异常值删除
money.delete_null()


######北向资金更新模块######


######龙虎榜更新模块######


######valudation更新模块######


######更新完成######
count_end = get_query_count()
print(f"更新完成 累计消耗条目数{count_start - count_end}")