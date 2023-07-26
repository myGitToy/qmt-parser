import numpy as np
import pandas as pd
import tushare as ts
from datetime import datetime,timedelta
from apt.vendor.tspro.security import security  as security
from apt.vendor.akshare.data import data as data
from apt.vendor.tspro.money_flow import money_flow as money

#1. 初始化
a = data(myauth = True)
ak = data(myauth = True)
a.code = ak.code = '600038.sh'
a.start_date = ak.start_date =  datetime(2023,7,27,8) #1998/10/20日开始有ETF数据    ETF日线数据和复权数据已更新完毕
a.end_date = ak.end_date =  datetime.now()
#2. 更新证券代码库(stock和ETF资产)
sec = security()
sec.update_security()
sec.update_security_ETF()

#更新交易日历
sec.update_calendar()

#更新资金流向
flow = money()
flow.start_date = a.start_date
flow.end_date = a.end_date
flow.daily_update(sleep = 0.2)

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
ak.update_sequence_add(myclass = 'stock' , type = '60m' , priority = 0) #更新stock
ak.update_sequence_add(myclass = 'etf' , type = '60m' , priority = 0) #更新etf

ak.ktype = '5m' #更新5分钟线 起始日期2023/4/26
ak.update_sequence_add(myclass = 'stock' , type = '5m' , priority = 0) #更新stock
ak.update_sequence_add(myclass = 'etf' , type = '5m' , priority = 0) #更新etf

ak.ktype = '1m' #更新5分钟线 起始日期2023/6/7
ak.update_sequence_add(myclass = 'stock' , type = '1m' , priority = 1) #更新stock
ak.update_sequence_add(myclass = 'etf' , type = '1m' , priority = 1) #更新etf