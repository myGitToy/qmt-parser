from apt.qsp_universal.base import base as base
from apt.vendor.jqdata.jqdata import data as jqdata
from datetime import datetime 
a = base()
a.code = '600038.sh'
a.ktype = '1m'
a.start_date = datetime(2020,1,1)
a.end_date = datetime(2022,7,1)
a.fq = a.复权.前复权
#print(a.fq)
a.myauth = False
a.vendor = base.vendor.tusharePro
df = a.get_k_data()
print(df)

