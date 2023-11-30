"""
资金流向日常更新更新模块
更新以下数据：
资金流向

"""
import pandas as pd
import numpy as np
from datetime import datetime
from apt.qsp_universal.base import base as data
from apt.vendor.akshare.data import data as akdata
from apt.vendor.akshare.money_flow import money_flow as money_flow
from apt.vendor.tspro.security import security as sec
#pd.set_option('display.max_rows',   None)
#pd.set_option('display.max_columns', None)


money = money_flow()
money.start_date = datetime(2022,7,1)
money.end_date = datetime.now()
#更新资金流向（由于资金流向更新时间比较迟，因此此处再次进行差值更新）
money.daily_update(sleep = 0.2)
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
#数据去重
df_code_main.drop_duplicates(subset = ['证券代码'], keep = 'first', inplace = True)
#print(df_code_main)

df_main = pd.DataFrame() 
n = 0
print("#############开始更新资金流向数据####################")
for code in df_code_main['证券代码']:
    #print(sec.get_security(money , code = code)[1])
    if sec.get_security(money , code = code)[1] in ['stock','etf']:
        #akshare的资产类别可以支持stock和etf，这里为了保持代码的一致性，因此保留原来的判定
        name = df_code_main.iloc[n].at['证券名称']
        print(f'正在更新：{name} {n}/{df_code_main.shape[0]}')
        money.code = code
        df = money.get_money_flow_1min()
        df_main = pd.concat([df_main, df] , sort = False)
    n = n + 1
df_main.to_csv('.\\data\\海龟模型\\资金流向（ak1分钟线）.csv', encoding = 'utf_8_sig')