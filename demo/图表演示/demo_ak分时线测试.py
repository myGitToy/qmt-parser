from datetime import datetime, timedelta
import pandas as pd
import akshare as ak
from apt.vendor.akshare.data import data as ak_data

#df_ak = pd.DataFrame()
symbol = '839167'
start_date = datetime(2025, 4, 20, 8)
end_date = datetime(2025, 4, 30, 18)
ktype='1'
df_ak =  ak.stock_zh_a_hist_min_em(symbol = symbol , start_date = start_date.strftime('%Y%m%d %H:%M:%S'), end_date = end_date.strftime('%Y%m%d %H:%M:%S'), period = ktype, adjust='')
print(df_ak)