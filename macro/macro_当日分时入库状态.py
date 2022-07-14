from datetime import datetime
import tushare as ts
from apt.vendor.tspro.data import data
a = data()
nw = datetime.now()
a.start_date = datetime(nw.year,nw.month,nw.day,8)
a.end_date = datetime(nw.year,nw.month,nw.day,16)
df_tspro = ts.pro_bar(api = a.api , ts_code = '601318.sh', freq = '1min' , adj = None , start_date = a.start_date.strftime('%Y-%m-%d %H:%M:%S') , end_date = a.end_date.strftime('%Y-%m-%d %H:%M:%S') , adjfactor = True , factors = ['tor', 'vr'] , asset = 'E')
print(df_tspro)
