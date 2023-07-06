from apt.vendor.akshare.data import data as data
from apt.qsp_universal.base import base as qsp_base
from datetime import datetime
import pandas as pd
# 显示所有行
pd.set_option('display.max_rows', None)

#测试akshare数据获取模块
a = data()
a.start_date= datetime(2023,6,15,8)
a.end_date = datetime(2023,6,15,16)
a.ktype = '1m'
a.code = '601128.SH'
df = a.get_k_data()
print(df)

#测试通用数据获取模块
qsp = qsp_base()
qsp.start_date= datetime(2023,6,15,8)
qsp.end_date = datetime(2023,6,15,16)
qsp.ktype = '1m'
qsp.vendor = qsp_base.vendor.akshare
qsp.code = '601128.SH'
df_qsp = qsp.get_k_data()
print(df_qsp)