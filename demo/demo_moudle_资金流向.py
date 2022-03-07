"""
本模块用于测试主力流出资金占到总流通市值的比例，并作图
"""
import datetime
from jqdatasdk import *
import pandas as pd
import datetime
import sqlalchemy
from apt.vendor.jqdata.base import base as base
from apt.vendor.jqdata.jqdata import data as jqdata

#基础设置
jq = jqdata(myauth = False)
jq.start = datetime.datetime(2010,1,1)
jq.end = datetime.datetime.now()
jq.code = '601888.XSHG'
jq.mystr = ''


#######1. 加载不同的自选股列表（数据更新时不能打开相关的excel文件，否则读取权限会显示失败）
code_df1 = jqdata.read_excel(file_name = '.\\data\\海龟模型\\自选股列表.xlsx' , sheet_name = '33指数')
code_df2 = jqdata.read_excel(file_name = '.\\data\\海龟模型\\自选股列表.xlsx' , sheet_name = 'ETF')

#######1.1 合并自选股列表并去重
code_df = pd.concat([code_df1, code_df2],sort = True)
code_df.rename(columns={'证券代码':'code'} , inplace = True)
code_df.drop_duplicates(subset = 'code' , inplace = True , keep = 'first')  
print(code_df)

#######1.2 获取证券名称信息，去除其中的etf
df_name = pd.read_sql_query(f"select code,display_name,type from jqdata_security" , jq.engine)
print(df_name)
code_list = pd.merge(code_df , df_name , on = ['code'] , how = 'left')
code_list = code_list.loc[code_list['type']=='stock']
#去除重复的名字并排序
code_list.sort_values(by = 'code' , inplace = True)
code_list = code_list[['code','display_name','type']]
print(code_list)
#
#获取代码列表
code_list1 = list(set(code_list['code']))

#用于存盘的主文件
df_main = pd.DataFrame()
#增加代码名称列
#df_name_list['name']=0
#设定DataFrame，用于储存代码和名称
n = 1
for code in code_list1:
    #获取收盘信息
    print(f'正在获取{code} {n}/{len(code_list1)}')
    n = n + 1
    df = jq.get_k_data(code = code)
    #获取流通市值信息
    df_val = pd.read_sql_query(f"select code,date,circulating_market_cap from valuation where code = '{code}' order BY date" , jq.engine)
    df = pd.merge(df,df_val,on = ['code','date']) 

    #获取资金流向
    df_money_flow = pd.read_sql_query(f"select code,date,net_amount_main from jqdata_money_flow where code = '{code}' order BY date" , jq.engine)
    df = pd.merge(df,df_money_flow,on = ['code','date']) 

    #5日资金流向
    df['main5'] = df['net_amount_main'].rolling(5).mean()

    #5日资金与流通市值占比
    df['main5_cap'] = df['main5'] / df['circulating_market_cap'] / 10000

    #合并文件
    df_main = pd.concat([df_main, df],sort = False)




    #name = get_security_info(code).display_name
    #给指定单元格赋值
    #df_name_list.loc[df_name_list['code']==code,'name'] = name

df_main = pd.merge(df_main , code_list , on = ['code'] , how = 'left')
print(df_main)
df_main.to_excel('.\\data\\测试数据\\资金流向.xlsx', sheet_name = '5日平均主力动向' ,  header=True, index=False)