"""
海龟模型日常更新模块
更新以下数据：
自选股列表
ATR数据
Prank数据

"""
import pandas as pd
from datetime import datetime
import numpy as np
from jqdatasdk import *
from backtrader import talib
from apt.qsp_universal.atr import ATR
from apt.qsp_universal.k import k
#from apt.vendor.jqdata.jqdata import data
from apt.qsp_universal.base import base as data
from apt.vendor.tspro.data import data as tsdata
from apt.qsp_universal.prank import prank
from apt.qsp_universal.expma import expma as EXP

#pd.set_option('display.max_rows',   None)
#pd.set_option('display.max_columns', None)


a = ATR()
rank = prank()
exp = EXP()
a.ktype = rank.ktype = exp.ktype = '1d'
a.start_date = rank.start_date = exp.start_date = datetime(2022,1,1)    #本地数据读取的开始日期，缩小间隔可减少excel文件的体积
a.end_date  = rank.end_date = exp.end_date = datetime.now()
a.vendor  = rank.vendor = exp.vendor = a.vendor.tusharePro

#######00. 前置更新 更新交易日历
#更新交易日历
#cal = data()
#cal.update_trader_days()
#df = a.k_new_high_count()
#print(df[['date','close','new_high','new_high_count']])
#######1. 加载不同的自选股列表（数据更新时不能打开相关的excel文件，否则读取权限会显示失败）
df_code_main = pd.DataFrame()
#读取第一张表格
df_code1 = data.read_excel(file_name = '.\\data\\海龟模型\\自选股列表.xlsx' , sheet_name = '33指数')
#读取第二张表格
df_code2 = data.read_excel(file_name = '.\\data\\海龟模型\\自选股列表.xlsx' , sheet_name = '自选股')
#读取第三张表格
df_code3 = data.read_excel(file_name = '.\\data\\海龟模型\\自选股列表.xlsx' , sheet_name = 'ETF')
#合并表格
df_code_main = pd.concat([df_code_main, df_code1 , df_code2 , df_code3] , sort = False)
print(df_code_main)
df = df_code_main.query('证券代码 == "688349.SH"')
print(df)
#更改列名
df_code_main.rename(columns={"证券代码": "code", "证券名称": "name"} , errors="raise" , inplace = True)
#去重
df_code_main.drop_duplicates(subset = ['code'], keep = 'first', inplace = True)
#证券代码列表
code_list = df_code_main['code'].tolist()
#print(df_code_main )

#更新日线和60分钟线数据
dt = tsdata(myauth = True)
#a = data(myauth = True)
dt.start_date = datetime(2023,4,2,8) #数据更新的开始日期
dt.end_date = datetime.now()
dt.ktype = '60m'
dt.update_sequence_add(code_list = code_list , type = '60m')
dt.ktype = '1m'
dt.update_sequence_add(code_list = code_list , type = '1m')
dt.update_sequence_launch(priority = 1)


#######3. 获取ATR数据
df_atr = a.daily_update(code_list = code_list , N = 45 , to_csv = False)
#print(df_atr)
#ATR数据增加一个证券名称task:232(ps:加错地方了，但是考虑到excel文件已经修改，因此保留)
df_atr = pd.merge(df_atr , df_code_main[['code','name']] , how = 'left' , on = 'code')

#######4. ATR数据存盘
#df_atr.to_excel('.\\data\\海龟模型\\海龟模型JQDATA.xlsx', sheet_name='RAW_ATR',  header=True, index=False)
df_atr.to_csv('.\\data\\海龟模型\\ATR_tspro.csv', encoding = 'utf_8_sig')

#######5. 获取PRANK数据
df_prank = rank.daily_update(code_list = code_list , N = 180 , to_csv = False)

#######5.5 对Prank数据进行进一步处理，增加P75ATR数据
#取atr数据
df_atr.rename(columns={'date':'day'} , inplace = True)
#日期转换为datetime64[ns] 否则会在merge操作中因为两列属性不同和无法完成合并操作
df_atr['day'] = pd.to_datetime(df_atr['day'])
#取prank数据
#日期转换为datetime64[ns] 否则会在merge操作中因为两列属性不同和无法完成合并操作
df_prank['date'] = pd.to_datetime(df_prank['date'])
df_prank['day'] = df_prank['date'].dt.date
df_prank['day'] = pd.to_datetime(df_prank['day'])
#print(f"原始数据行数：{df_prank.shape[0]}；列数：{df_prank.shape[1]}")
#合并并增加P75ATR信息
df_prank = pd.merge(df_prank , df_atr[['day','code','ATR']] , on = ['day','code'] ) 
#print(f"更新后数据行数：{df_prank.shape[0]}；列数：{df_prank.shape[1]}")
#df_prank['p75ATR'] = df_prank['p75'] / df_prank['ATR']
df_prank['p75ATR'] = (df_prank['close'] - df_prank['p75'] ) / df_prank['ATR']
#prank数据增加一个证券名称task:232
df_prank = pd.merge(df_prank , df_code_main[['code','name']] , how = 'left' , on = 'code')

#######6. PRANK数据存盘(新版本加入P75ATR列)
#df_prank.to_csv('.\\data\\海龟模型\\prank_jqdata_tmp.csv', encoding = 'utf_8_sig')
df_prank.to_csv('.\\data\\海龟模型\\prank_tspro.csv', encoding = 'utf_8_sig')

#######7. 更新EXPMA数据
df_exp = exp.daily_update(code_list = code_list , to_csv = True)

print('海龟模型更新完毕！')