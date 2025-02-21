import akshare as ak
from datetime import datetime,timedelta
from apt.vendor.akshare.data import data as ak_data
a = ak_data()
a.start_date = datetime(2025,2,12,8)
a.end_date = datetime.now()
a.code = 'sh.600038'
df_ak =  ak.stock_zh_a_hist_min_em(symbol = a.code , start_date = a.start_date.strftime('%Y%m%d %H:%M:%S'), end_date = a.end_date.strftime('%Y%m%d %H:%M:%S'), period = '1m', adjust = '')
print(df_ak)