"""
获取历史的分时数据 1000条左右
https://tushare.pro/document/2?doc_id=374
"""
import tushare as ts
import os
from datetime import datetime
from apt.vendor.tspro.security import security
from apt.vendor.tspro.finance_indicator import finance_indicator
from apt.vendor.tspro.data import data as data
from apt.vendor.tspro.base import base as base
from dotenv import load_dotenv #用于读取.env文件	
a = base()

# 配置API TOKEN
load_dotenv()
token = os.getenv("TUSHARE_TOKEN", "default token here").strip()
ts.set_token(token)


df_rt_min = a.pro.rt_min(ts_code='600000.SH', freq='5MIN')
print(df_rt_min)
"""
rt_min A股实时分钟
ts_code  freq                 time  open  close  high   low        vol      amount
0  600000.SH  1MIN  2025-07-11 15:00:00  13.8   13.8  13.8  13.8  5033118.0  69457028.0
"""


#df_realtime_quote = ts.realtime_quote(ts_code='600000.SH')
#print(df_realtime_quote)
"""
接口：realtime_quote 实时盘口TICK快照
"""


df_realtime_tick = ts.realtime_tick(ts_code='600000.SH')
print(df_realtime_tick)
"""
接口：realtime_tick
"""


