from apt.qsp_jqdata.A import A as A
from apt.vendor.jqdata.jqdata import data as data
from datetime import datetime
import pandas as pd
import tushare as ts
import talib as ta




#from jqlib.technical_analysis import *
a= A()
a.code = '601318.XSHG'
a.start = datetime(2021,1,1)
a.end = datetime(2021,10,26)
a.myauth = False
#df = a.A04B01_EMA均线数据()
#测试A04B04
#df = a.A04B05_EMA均线_收盘价小于均线(ma = '120', adjust_N = 10 , count = 10)

#测试A04B06
df = a.A04B06_EMA均线_线性回归角度(ma = '20', adjust_N = 20 , count = 16)
print(df)

#测试均线多头排列
df = a.A01B01_MA均线数据()
df['cl'] = ta.CDL2CROWS(df['open'],df['high'],df['low'],df['close'])
print(df)
print(df[['code','date','close','MA5','MA10','MA20']])
#print(f'均线是否空头排列：{df}')
