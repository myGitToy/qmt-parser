from apt.qsp_jqdata.A import A as A
from datetime import datetime
import pandas as pd
import tushare as ts
import talib as ta

#from jqlib.technical_analysis import *
a= A()
a.code = '601318.XSHG'
a.start = datetime(2021,1,1)
a.end = datetime(2021,11,3)
a.myauth = False

#df = a.A04B01_EMA均线数据()

#测试均线多头排列
df = a.A01B01_MA均线数据()
print(df[['code','date','close','MA5','MA10','MA20']])
#print(f'均线是否空头排列：{df}')
