import pandas as pd
import datetime
from backtrader import talib
from apt.qsp_jqdata.atr import ATR
from apt.qsp_jqdata.k import k
from apt.vendor.jqdata.jqdata import data
from apt.qsp_jqdata.prank import prank


####1. ATR数据读取####
df_atr = pd.read_csv('.\\data\\海龟模型\\ATR_jqdata.csv', encoding = 'utf_8_sig')[['date','code','close','ATR']]
df_atr.rename(columns={'date':'day'} , inplace = True)
print(df_atr)
#日期转换为datetime64[ns] 否则会在merge操作中因为两列属性不同和无法完成合并操作
df_atr['day'] = pd.to_datetime(df_atr['day'])

####2. PRANK数据读取####
df_prank = pd.read_csv('.\\data\\海龟模型\\prank_jqdata.csv', encoding = 'utf_8_sig')
#日期转换为datetime64[ns] 否则会在merge操作中因为两列属性不同和无法完成合并操作
df_prank['date'] = pd.to_datetime(df_prank['date'])
df_prank['day'] = df_prank['date'].dt.date
df_prank['day'] = pd.to_datetime(df_prank['day'])
print(df_prank)

df_merge = pd.merge(df_atr[['day','code','close','ATR']],df_prank[['day','code','p75']] , on = ['day','code']) 
df_merge['p75ATR'] = (df_merge['p75'] - df_merge['close']) / df_merge['ATR']
print(df_merge[df_merge['code'] == '512760.XSHG'])