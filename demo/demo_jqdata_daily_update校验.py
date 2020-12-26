from jqdatasdk import *
import pandas as pd
import datetime
import sqlalchemy
from apt.vendor.jqdata.jqdata import data as jqdata
from apt.vendor.jqdata.ETF import ETF as ETF

"""
校验日线数据 建议每月运行一次
每个交易日的校验需耗时约35-40秒
"""

start = datetime.datetime(2020,12,22) 
end = datetime.datetime.now()
jq = jqdata(rds_host = jqdata.数据源.localhost)
df_remain = get_query_count()
print(df_remain)
#更新日线
jq.update_v1(start_date = start , end_date = end , ktype = '1d' )



