import numpy as np
import pandas as pd
import tushare as ts
from datetime import datetime,timedelta
from apt.vendor.tspro.security import security  as security
from apt.vendor.tspro.data import data as data

#1. 初始化
a = data(myauth = True)
a.code ='600038.sh'
a.start_date= datetime(2021,1,1)
a.end_date = datetime(2022,7,9)
#2. 更新证券代码库
sec = security()
sec.update_security()

#更新交易日历
sec.update_calendar()

#3. 更新股票日线数据和复权因子(2021/1/1)    最后更新日期2022/7/1含
a.ktype = '1d'
#a.update_day()
a.update_factor()

#4. 更新股票小时线数据   60分钟线最后更新日期2022/7/1含；5分钟线2020全年写入更新序列
#目前更新序列剩余18700，预计耗时13小时（每分钟预计可更新24-27组，每组约5800条左右）
a.ktype = '1m'
#a.update_sequence_add(type = '1d')
a.update_sequence_launch()
#5. 更新ETF日线数据

#6. 更新ETF小时线数据
