import numpy as np
import pandas as pd
import tushare as ts
from datetime import datetime,timedelta
from apt.vendor.tspro.security import security  as security
from apt.vendor.tspro.data import data as data

#1. 初始化
a = data(myauth = True)
a.code ='600038.sh'
a.start_date= datetime(2021,6,20)
a.end_date = datetime(2022,6,1)
#2. 更新证券代码库
#sec = security()
#security.update_security(a)

#更新交易日历


#3. 更新股票日线数据    最后更新日期2021/6/20含
#a.ktype = '1d'
#a.update_day()

#4. 更新股票小时线数据   60分钟线最后更新日期2022/7/1含；5分钟线2020全年写入更新序列
#目前更新序列剩余51530，预计耗时32小时
a.ktype = '1m'
a.update_sequence_add(type = '1d')
a.update_sequence_launch()
#5. 更新ETF日线数据

#6. 更新ETF小时线数据
