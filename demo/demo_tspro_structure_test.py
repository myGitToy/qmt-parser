from datetime import datetime 
from apt.vendor.tspro.data import data as data

a = data(myauth = True)
#a.myauth = False
a.code = '600038.sh'
a.start_date = datetime(2012,8,2)
print(a.myauth)
a.end_date = datetime.now()
a.fq = data.复权.不复权
df = a.pro.pro_bar(ts_code = '510300.sh', start_date = '20220610' , end_date = '20220613')
print(df)
a.update_v1()
#a.ktype = '1d'
print(a.ktype)
print(a.fq)
cal = a.update_v1()
df = a.get_k_data()
print(df)
