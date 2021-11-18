"""
海龟模型日常更新模块
更新以下数据：
自选股列表
ATR数据
Prank数据

"""
import pandas as pd
import datetime
from jqdatasdk import *
from backtrader import talib
from apt.qsp_jqdata.atr import ATR
from apt.qsp_jqdata.k import k
from apt.vendor.jqdata.jqdata import data
from apt.qsp_jqdata.prank import prank
from apt.qsp_jqdata.expma import expma as EXP

pd.set_option('display.max_rows',   None)
pd.set_option('display.max_columns', None)
a = ATR()
rank = prank()
a.myauth = False
auth('18621899367','Qq19840207')
#a.code = '601318.XSHG'
a.ktype = '1d'
a.start = datetime.datetime(2020,11,1)
a.end = datetime.datetime.now()
#df = a.k_new_high_count()
#print(df[['date','close','new_high','new_high_count']])
#######1. 加载不同的自选股列表（数据更新时不能打开相关的excel文件，否则读取权限会显示失败）
code_list1 = data.read_excel(file_name = '.\\data\\海龟模型\\自选股列表.xlsx' , sheet_name = '33指数')['证券代码'].tolist()
code_list2 = data.read_excel(file_name = '.\\data\\海龟模型\\自选股列表.xlsx' , sheet_name = 'ETF')['证券代码'].tolist()

#######2. 合并自选股列表并去重
code_list1.extend(code_list2)
#获取代码列表
code_list = list(set(code_list1))

#名字列表初始化并且获取数据
df_list_tmp = {'code':code_list}
df_name_list = pd.DataFrame(df_list_tmp)
#增加代码列
df_name_list['name']=0
#设定DataFrame，用于储存代码和名称
for code in code_list:
    name = get_security_info(code).display_name
    #给指定单元格赋值
    df_name_list.loc[df_name_list['code']==code,'name'] = name

#更新日线和60分钟线数据
update_start = datetime.datetime(2021,11,10)
jq = data(rds_host = data.数据源.localhost , myauth = True )
jq.update_v2(code_list = code_list , start_date = update_start , end_date = a.end , ktype = '1d' )
jq.update_v2(code_list = code_list , start_date = update_start , end_date = a.end , ktype = '60m' )

#######3. 获取ATR数据
df_atr = a.daily_update(code_list = code_list , N = 25 , to_csv = False)
#ATR数据增加一个证券名称task:232(ps:加错地方了，但是考虑到excel文件已经修改，因此保留)
df_atr = pd.merge(df_atr,df_name_list,how='left',on = 'code')

#######4. ATR数据存盘
#df_atr.to_excel('.\\data\\海龟模型\\海龟模型JQDATA.xlsx', sheet_name='RAW_ATR',  header=True, index=False)
df_atr.to_csv('.\\data\\海龟模型\\ATR_jqdata.csv', encoding = 'utf_8_sig')
#######5. 获取PRANK数据
df_prank = rank.daily_update(code_list = code_list , N = 100 , to_csv = False)

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
print(f"原始数据行数：{df_prank.shape[0]}；列数：{df_prank.shape[1]}")
#合并并增加P75ATR信息
df_prank = pd.merge(df_prank , df_atr[['day','code','ATR']] , on = ['day','code'] ) 
print(f"更新后数据行数：{df_prank.shape[0]}；列数：{df_prank.shape[1]}")
#df_prank['p75ATR'] = df_prank['p75'] / df_prank['ATR']
df_prank['p75ATR'] = (df_prank['close'] - df_prank['p75'] ) / df_prank['ATR']
#prank数据增加一个证券名称task:232
df_prank = pd.merge(df_prank,df_name_list,how='left',on = 'code')

#######6. PRANK数据存盘(新版本加入P75ATR列)
#df_prank.to_csv('.\\data\\海龟模型\\prank_jqdata_tmp.csv', encoding = 'utf_8_sig')
df_prank.to_csv('.\\data\\海龟模型\\prank_jqdata.csv', encoding = 'utf_8_sig')

#######7. 更新EXPMA数据
exp = EXP()
exp.start = a.start
exp.end = a.end
exp.ktype ='1d'
df_exp = exp.daily_update(code_list = code_list)