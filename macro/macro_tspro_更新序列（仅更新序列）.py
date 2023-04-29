import numpy as np
import pandas as pd
import tushare as ts
from datetime import datetime,timedelta
from apt.vendor.tspro.security import security  as security
from apt.vendor.tspro.data import data as data
#pd.set_option('display.max_columns', None)
#pd.set_option('display.max_rows', None)
#1. 更新序列
a = data()
a.start_date= datetime(2021,6,1)
a.end_date = datetime.now()
#a.update_etf_day()
#优先更新高权限序列
a.update_sequence_launch(priority = 1)
a.update_sequence_launch(priority = 0) 

