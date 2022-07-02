from apt.qsp_universal.base import base as base
from apt.vendor.jqdata.jqdata import data as jqdata
a = base()
a.code = '600038.sh'
a.start_date = '2021/1/1'
a.end_date = '2022/1/1'
a.fq = jqdata.复权.动态复权
a.myauth = False
a.vendor = base.vendor.tusharePro
df = a.get_k_data()
print(df)

