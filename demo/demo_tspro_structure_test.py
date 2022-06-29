from datetime import datetime 
from apt.vendor.tspro.data import data as data
import pandas as pd
import tushare as ts
# 列名与数据对其显示
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
# 显示所有列
pd.set_option('display.max_columns', None)

a = data(myauth = True)
#a.myauth = False
a.code = '600038.sh'
#a.start_date = datetime(2016,7,10)  #日线更新起始日期

a.start_date = datetime(2021,1,1)
a.end_date = datetime.now()

a.fq = data.复权.不复权
a.ktype = '60m'
#a.update_day()
a.update_min()  
#a.ktype = '1d'
print(a.ktype)
print(a.fq)
cal = a.update_v1()
df = a.get_k_data()
print(df)
