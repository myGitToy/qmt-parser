import numpy as np
import pandas as pd
import tushare as ts
from datetime import datetime,timedelta
from apt.vendor.tspro.security import security  as security
from apt.vendor.akshare.data import data as ak_data
from apt.vendor.tspro.base import base as tspro_base
from apt.vendor.tspro.data import data as tspro_data
from apt.vendor.tspro.money_flow import money_flow as money
from apt.vendor.tspro.cumulative_turnover import cum_turnover as ct
from apt.os.hdf5 import hdf5 as hdf5
"""
每日更新目前需要完成的工作：
1. 日线数据更新 重刷一编 2023/1/1 - 2023/12/11
2. 基础信息daily basic数据库重建及更新  Checked
3. 资金流向数据库重建及更新 Checked
4. 解决sec.get_basic(to_csv = True)的问题：没有此目录文档
5. 由上述文件引出的话题，可能海龟模型等一系列文件都需要重建，或者和azure Ops一起解决
6. 确认akshare数据库中缺失的日期段
    60m：自2023/10/27起-2023/12/11
    5m：自2023/10/27起
    1m：自2023/12/4起
"""
#1. 初始化
a = hdf5()  # 初始化hdf5类
#全市场数据校验下次起始日期2023/12/13
#2023年已完成校验 2022可能还需要校验
#2024/1/1-2024/9/20前已完成校验
a.start_date =  datetime(2025,7,2,8) #1998/10/20日开始有ETF数据    ETF日线数据和复权数据已更新完毕
a.end_date =  datetime.now()


################# 基础数据准备：获取全部证券代码（）
#df_all_code = security.get_all_code(ak) #从本地数据库获取
base = tspro_base()  # 使用tspro_base获取数据
#从tspro api获取证券类代码 正常情况下约5419
df_stock = base.pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
# 获取ETF类代码 正常情况下约2200
df_etf = base.pro.fund_basic(market='E')

# 合并
df_all_code = pd.concat([df_stock, df_etf], ignore_index=True)
# 重命名列 ts_code为code
df_all_code.rename(columns={'ts_code': 'code'}, inplace=True)
# 输出code列
# print(df_all_code['code'])
#------------------------------------------#



a.update_sequence_add (code_list=df_all_code['code'].tolist(), type = '1m' , priority = 1) #更新stock