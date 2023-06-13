from apt.vendor.akshare.data import data as data
from datetime import datetime
import pandas as pd
# 显示所有行
pd.set_option('display.max_rows', None)
a = data()
a.start_date= datetime(2023,5,20,8)
a.end_date = datetime(2023,6,7,16)
a.ktype = '60m'
a.code = '601128.SH'
df = a.get_k_data()
print(df)