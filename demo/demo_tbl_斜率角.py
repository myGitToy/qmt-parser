"""
测试talib数据库中的函数
talib库提供LINEARREG_ANGLE函数用以计算线性回归的角度，LINEARREG_SLOPE函数用以计算线性回归斜率
"""

from apt.qsp_jqdata.A import A as A
from apt.vendor.jqdata.jqdata import data as data
from datetime import datetime
import pandas as pd
import tushare as ts
import talib as ta
import numpy as np
pd.set_option('display.max_rows', None)


#from jqlib.technical_analysis import *
a= A()
a.code = '300041.XSHE'
a.start = datetime(2021,1,1)
a.end = datetime(2021,11,23)
a.myauth = False
#df = a.A04B01_EMA均线数据()
#获取EMA均线数据
df = a.A04B01_EMA均线数据()
#talib库提供LINEARREG_ANGLE函数用以计算线性回归的角度，LINEARREG_SLOPE函数用以计算线性回归斜率
#基于EMA20 timeperiod=2的数据研究，3以内数据平台整理，出现大于5开始有突破动作
#用period2比较理想，其他数据均有较大延迟，建议使用N天内出现X次的思路
#df['EMA_ANGLE'] = ta.LINEARREG_ANGLE(df['EMA20'] , timeperiod = 2)
df['TSF'] = ta.TSF(df['EMA20'] , timeperiod = 20)
df['EMA_SLOPE'] =(df['EMA20'] - df[f'EMA20'].shift(1)) / df[f'EMA20'].shift(1)
#df['x_s'] = ta.LINEARREG_SLOPE(df['EMA20'] , timeperiod = 2)
print(df)
#print(df[['date','code','close','EMA20','EMA_ANGLE','x_s']])