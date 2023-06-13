from datetime import datetime
import tushare as ts
from apt.vendor.tspro.data import data
a = data()
nw = datetime.now()
a.start_date = datetime(2023,5,12,8)
#print(a.start_date)
a.end_date = datetime(2023,5,12,16)
df_tspro60 = ts.pro_bar(api = a.api , ts_code = '601318.sh', freq = '60min' , adj = None , start_date = a.start_date.strftime('%Y-%m-%d %H:%M:%S') , end_date = a.end_date.strftime('%Y-%m-%d %H:%M:%S') , adjfactor = True , factors = ['tor', 'vr'] , asset = 'E')
df_tspro1 = ts.pro_bar(api = a.api , ts_code = '601318.sh', freq = '1min' , adj = None , start_date = a.start_date.strftime('%Y-%m-%d %H:%M:%S') , end_date = a.end_date.strftime('%Y-%m-%d %H:%M:%S') , adjfactor = True , factors = ['tor', 'vr'] , asset = 'E')
print(df_tspro1)
print(df_tspro60)
