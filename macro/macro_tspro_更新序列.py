import numpy as np
import pandas as pd
import tushare as ts
import sqlalchemy
import akshare as ak
from datetime import datetime,timedelta
from apt.vendor.tspro.security import security  as security
from apt.vendor.tspro.data import data as data

#1. 初始化
a = data()
a.code ='600038.sh'
a.start_date= datetime(2021,1,1)
a.end_date = datetime(2022,6,1)

#2. 更新证券代码库

#3. 更新股票日线数据

#4. 更新股票小时线数据

#5. 更新ETF日线数据

#6. 更新ETF小时线数据
