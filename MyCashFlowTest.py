# -*- coding: utf-8 -*-
from datetime import datetime,timedelta
import numpy as np
import pandas as pd
import tushare as ts
from MySTP import STP

#载入交割单
stp=STP(code_list = ['510300','510500','159949','512760','512880','512290','512580','512980','600460','000651','601318'],start = '2020-01-01',account_amount=1000000,account_risk=0.25)
df_trans = stp.get_transactions_info(start = stp.start)
df_trans['交收日期'] = pd.to_datetime(df_trans['交收日期'])

#载入300ETF获取交易日信息
df_day = pd.read_csv(('.\\data\\day\\510300.csv'))
df_day.rename(columns={ 'date' : '交收日期'} , inplace = True)
df_day['交收日期'] = pd.to_datetime(df_day['交收日期'])
df_day = df_day.set_index('交收日期')
df_day = df_day[df_day.index>=stp.start]['close']


"""
#定义证券代码列表
code_list = ['510300','510500','159949','512760','512880','512290','512580','512980']
#读取数据
df_day = pd.DataFrame()
for code in code_list:
    df = pd.read_csv('.\\data\\day\\%s.csv' % (code))
    df = df[['date','code','open','close','high','low','volume']]
    #print(df)
    df_day = pd.concat([df_day, df],sort = False)
    df_day = df_day[df_day['date']>=stp.start]
"""

#print(df_day)
#建立买卖记录的矩阵
#df_xxx = pd.DataFrame(index=df_day.values.tolist(),columns=['成交数量'])

#汇总交收数据 按日期和代码
#df_trans['交收日期'] = pd.to_datetime(df_trans['交收日期'])
df_trans = df_trans.groupby(['交收日期','证券代码']).sum()
print(df_trans)
df_day = pd.merge(df_day , df_trans , on = ['交收日期'], how = 'left')  
print(df_day)
pv = pd.pivot_table(df_day, index=['交收日期'] ,values = ['成交数量'],aggfunc=np.sum )
print(pv)
#df_xxx=df_xxx.combine_first(df_trans)
#df_xx =df_trade_log.fillna(0)
#print(df_xxx)