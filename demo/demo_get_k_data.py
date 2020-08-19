import pandas as pd
import tushare as ts
ts.set_token('55297f16c0119146589e059db315ba28a9412e89ec9f91e538e655b2')
pro = ts.pro_api()
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows',   None)
#df = ts.pro_bar(ts_code='000651.SZ', adj='qfq',freq=60)
df = ts.get_k_data('000651')
print(df.head(10))
print(df)
print(len(df))