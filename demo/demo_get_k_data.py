import pandas as pd
import tushare as ts
from apt.qsp.base import base as k
from apt.qsp.vol import vol as v
ts.set_token('55297f16c0119146589e059db315ba28a9412e89ec9f91e538e655b2')
pro = ts.pro_api()
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows',   None)
#df = ts.pro_bar(ts_code='000651.SZ', adj='qfq',freq=60)
vol = v(code = '000063' , start = '2020-01-02' , end = '2020-09-17' , ktype = 5 )
df = vol.amount_between(LOW = 0 , HIGH = 8e8 , x_rolling = 4 )
print("测试数据")
print(df)

a = k(code = '159949' , start = '2020-01-02' , end = '2020-09-17' , ktype = '5' )
df = a.get_k_data()
print(df)
df = ts.get_k_data('000651')
print(df.head(10))
print(df)
print(len(df))