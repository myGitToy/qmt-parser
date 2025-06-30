from datetime import datetime
import tushare as ts
import akshare as ak
from apt.vendor.tspro.data import data
a = data()
nw = datetime.now()
a.start_date = datetime(nw.year,nw.month,nw.day,8)
#print(a.start_date)
a.end_date = datetime(nw.year,nw.month,nw.day,16)
"""
tspro代码，目前已失效
df_tspro60 = ts.pro_bar(api = a.api , ts_code = '601318.sh', freq = '60min' , adj = None , start_date = a.start_date.strftime('%Y-%m-%d %H:%M:%S') , end_date = a.end_date.strftime('%Y-%m-%d %H:%M:%S') , adjfactor = True , factors = ['tor', 'vr'] , asset = 'E')
df_tspro1 = ts.pro_bar(api = a.api , ts_code = '601318.sh', freq = '1min' , adj = None , start_date = a.start_date.strftime('%Y-%m-%d %H:%M:%S') , end_date = a.end_date.strftime('%Y-%m-%d %H:%M:%S') , adjfactor = True , factors = ['tor', 'vr'] , asset = 'E')
print(df_tspro1)
print(df_tspro60)
"""
#检查ak1分钟线
df_ak1 = ak.stock_zh_a_minute(symbol = 'sh601318',period = '5')
print(df_ak1)

