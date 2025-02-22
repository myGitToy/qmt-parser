#from apt.vendor.jqdata.stk2.stk_hk_hold_info import stk_hk_hold_info as bxzj
import numpy as np
import pandas as pd
import tushare as ts
import sqlalchemy
import datetime
import os   #用于读取文件目录
from dotenv import load_dotenv #用于读取.env文件
from jqdatasdk import *
from apt.vendor.jqdata.base import base as base
#a = bxzj()
#a.daily_update()
#读取.env文件
load_dotenv()
auth(os.getenv('JQDATA_USER'),os.getenv('JQDATA_PASSWORD'))
#显示所有列
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
day = '2021-04-8'
link ='310001'
df = finance.run_query(query(finance.STK_HK_HOLD_INFO).filter(finance.STK_HK_HOLD_INFO.day == day , finance.STK_HK_HOLD_INFO.link_id == link))
print(df)