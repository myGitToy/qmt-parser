import numpy as np
import pandas as pd
import tushare as ts
from datetime import datetime,timedelta
from apt.vendor.tspro.security import security  as security
from apt.vendor.akshare.data import data as ak_data
from apt.vendor.tspro.data import data as tspro_data
from apt.vendor.tspro.money_flow import money_flow as money
from apt.vendor.tspro.cumulative_turnover import cum_turnover as ct
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
a = ak = ak_data(myauth = True)
a.code = ak.code = '600038.sh'
#全市场数据校验下次起始日期2023/12/13
#2023年已完成校验 2022可能还需要校验
#2024/1/1-2024/9/20前已完成校验
a.start_date = ak.start_date =  datetime(2025,2,20,8) #1998/10/20日开始有ETF数据    ETF日线数据和复权数据已更新完毕
a.end_date = ak.end_date =  datetime.now()
#2. 更新证券代码库(stock和ETF资产)
sec = security()
sec.update_security()
sec.update_security_ETF()

#更新交易日历
sec.update_calendar()

#更新基础信息daily basic（1991年至今）nb             
#此数据库未删除，为老版本
sec.start_date = datetime(2024,11,20)
sec.update_basic(sleep = 0.2)
#sec.get_basic(to_csv = True)

#更新资金流向（2007年至今） 数据更新时间20：00
flow = money()
#此数据库未删除，为老版本
flow.start_date = datetime(2024,11,20)
flow.end_date = a.end_date
flow.daily_update(sleep = 0.2)

#更新累计成交数据库(目前库数据不全，2023年含零碎数据，2023年前数据无，计划更新自2006年以来的数据)
ct.insert_cumulative_turnover(a)

#3. 更新股票日线数据和复权因子（忽略）
a.ktype = '1d'
a.update_day(flag_verify_db = False)
a.update_factor(flag_verify_db = False)

#5. 更新ETF日线数据和复权因子
a.update_day_ETF()          #包含2020年起的数据
a.update_factor_ETF() 

#4. 更新股票小时线数据   60分钟线最后更新日期2022/7/6含；1分钟线2020全年写入更新序列
#此处的数据更新采用akshare数据源 2023/6/11
ak.ktype = '60m' #更新60分钟线 起始日期2023/4/27
ak.update_sequence_add(myclass = 'stock' , type = '60m' , priority = 0 ,auto_select = True) #更新stock
ak.update_sequence_add(myclass = 'etf' , type = '60m' , priority = 0) #更新etf

ak.ktype = '5m' #更新5分钟线 起始日期2023/4/26
ak.update_sequence_add(myclass = 'stock' , type = '5m' , priority = 0) #更新stock
ak.update_sequence_add(myclass = 'etf' , type = '5m' , priority = 0) #更新etf

ak.ktype = '1m' #更新5分钟线 起始日期2023/6/7
ak.update_sequence_add(myclass = 'stock' , type = '1m' , priority = 1) #更新stock
ak.update_sequence_add(myclass = 'etf' , type = '1m' , priority = 1) #更新etf 