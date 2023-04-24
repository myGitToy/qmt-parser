import numpy as np
import pandas as pd
import tushare as ts
from datetime import datetime,timedelta
from apt.vendor.tspro.security import security  as security
from apt.vendor.tspro.data import data as data

#1. 初始化
a = data(myauth = True)
a.code ='600038.sh'
a.start_date= datetime(2023,4,22,8) #1998/10/20日开始有ETF数据    ETF日线数据和复权数据已更新完毕
a.end_date = datetime.now()
#2. 更新证券代码库(stock和ETF资产)
sec = security()
sec.update_security()
sec.update_security_ETF()

#更新交易日历
sec.update_calendar()

#3. 更新股票日线数据和复权因子（忽略）
a.ktype = '1d'
a.update_day(flag_verify_db = False)          #最后更新日期2022/7/8含
a.update_factor(flag_verify_db = False)

#5. 更新ETF日线数据和复权因子
a.update_day_ETF()          #包含2020年起的数据  最后更新日期2022/7/8含
a.update_factor_ETF() 

#4. 更新股票小时线数据   60分钟线最后更新日期2022/7/6含；1分钟线2020全年写入更新序列
#目前更新序列剩余18700，预计耗时13小时（每分钟预计可更新24-27组，每组约5800条左右）
#每个月数据量约1.5GB（纯数据库 不含索引） 含索引约2.2GB/月
a.ktype = '60m'
a.update_sequence_add(myclass = 'stock' , type = '60m' , priority = 0) #更新stock 60分钟线 最后更新日期2022/7/8含

#6. 更新ETF小时线数据  包含2020/4/20起的数据
a.update_sequence_add(myclass = 'etf' , type = '60m' , priority = 0) #更新etf 60分钟线 最后更新日期 2022/7/8