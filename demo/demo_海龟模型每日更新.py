"""
海龟模型日常更新模块
更新以下数据：
自选股列表
ATR数据
Prank数据

"""
import pandas as pd
import datetime
from backtrader import talib
from apt.qsp_jqdata.atr import ATR
from apt.qsp_jqdata.k import k
from apt.vendor.jqdata.jqdata import data
from apt.qsp_jqdata.prank import prank

pd.set_option('display.max_rows',   None)
pd.set_option('display.max_columns', None)
a = ATR()
rank = prank()
a.myauth = False
#a.code = '601318.XSHG'
a.ktype = '1d'
a.start = datetime.datetime(2021,1,1)
a.end = datetime.datetime.now()
#df = a.k_new_high_count()
#print(df[['date','close','new_high','new_high_count']])
#1. 加载不同的自选股列表（数据更新时不能打开相关的excel文件，否则读取权限会显示失败）
code_list1 = data.read_excel(file_name = '.\\data\\海龟模型\\自选股列表.xlsx' , sheet_name='33指数')['证券代码'].tolist()
code_list2 = data.read_excel(file_name = '.\\data\\海龟模型\\自选股列表.xlsx' , sheet_name='ETF')['证券代码'].tolist()

#2. 合并自选股列表并去重
code_list1.extend(code_list2)
code_list = list(set(code_list1))

#更新日线和60分钟线数据
update_start = datetime.datetime(2021,4,9)
jq = data(rds_host = data.数据源.localhost , myauth = True )
jq.update_v2(code_list = code_list , start_date = update_start , end_date = a.end , ktype = '1d' )
jq.update_v2(code_list = code_list , start_date = update_start , end_date = a.end , ktype = '60m' )

#3. 获取ATR数据
df_atr = a.daily_update(code_list = code_list , N = 14 , to_csv =False)

#4. ATR数据存盘
#df_atr.to_excel('.\\data\\海龟模型\\海龟模型JQDATA.xlsx', sheet_name='RAW_ATR',  header=True, index=False)
df_atr.to_csv('.\\data\\海龟模型\\ATR_jqdata.csv', encoding = 'utf_8_sig')
#5. 获取PRANK数据
df_prank = rank.daily_update(code_list = code_list , N = 100 , to_csv =False)

#6. PRANK数据存盘
df_prank.to_csv('.\\data\\海龟模型\\prank_jqdata.csv', encoding = 'utf_8_sig')



