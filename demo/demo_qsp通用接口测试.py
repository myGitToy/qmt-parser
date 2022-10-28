from apt.qsp_universal.base import base as base
from apt.vendor.jqdata.jqdata import data as jqdata
from datetime import datetime 
a = base()
a.code = '002340.sz'
a.ktype = '1d'
a.start_date = datetime(2022,5,27)
a.end_date = datetime(2022,6,24)
a.fq = a.复权.动态复权
#print(a.fq)
a.myauth = False
a.vendor = base.vendor.tusharePro
df = a.get_k_data()
print(df)
max3 = df['close'].nlargest(n = 2 , keep = 'first').mean()
print(max3)

