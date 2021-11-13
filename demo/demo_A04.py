from apt.qsp_jqdata.A import A as A
from datetime import datetime
import pandas as pd
import tushare as ts
import talib as ta

#from jqlib.technical_analysis import *
a= A()
a.code = '601012.XSHG'
a.start = datetime(2021,1,1)
a.end = datetime.now()
a.myauth = False

df = a.A04B01_EMA均线数据()
print(df[['code','date','close','EMA5','EMA20','EMA60','EMA120']])
