#from apt.vendor.jqdata.stk2.stk_hk_hold_info import stk_hk_hold_info as bxzj
import numpy as np
import pandas as pd
import tushare as ts
import sqlalchemy
import datetime
from jqdatasdk import *
from apt.vendor.jqdata.base import base as base
#a = bxzj()
#a.daily_update()
auth('13817092632','JQ@tushare123')
#显示所有列
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
day = '2021-04-8'
link ='310001'
df = finance.run_query(query(finance.STK_HK_HOLD_INFO).filter(finance.STK_HK_HOLD_INFO.day == day , finance.STK_HK_HOLD_INFO.link_id == link))
print(df)