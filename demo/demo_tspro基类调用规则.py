"""
目前的调用存在很多问题：
基类的调用顺序是什么？有从qsp_jqdata这边引入的，有也从vendor.jqdata处引用的
如何调用，实例化和非实例化是有区别的；
前期每日数据导入和更新等调用程序大部分是非实际化调用，直接用jqdata.XXX进行调取，缺点是每次导入都要传入代码，日期等数据，不方便
后期采用部分实际化调用，用a=base() a.XXX进行调取
上述调用也存在一定的问题，尤其是涉及前期数据接口 localhost和auth T/F的处理
"""
from apt.vendor.tspro.data import data as tsdata
from apt.vendor.tspro.pro_api import pro_api
from datetime import datetime
a = tsdata(rds_host = tsdata.数据源.localhost , myauth = False)
a.code = '600519.SH'
a.start_date = datetime(2023,1,1)
a.end_date = datetime(2023,1,10)
a.ktype = '1d'
a.myauth = False
# = tsdata.数据源.centos9
df = a.get_k_data()
df2 = tsdata.get_k_data(a)
print(df)
print(df2)
