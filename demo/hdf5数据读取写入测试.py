from datetime import datetime
import tushare as ts
import pandas as pd
from apt.vendor.tspro.data import data
a = data()
nw = datetime.now()
a.start_date = datetime(2000,1,1,8)
a.end_date = datetime(2022,1,1,8)
#用token从TS PRO服务器端读取 ，最大8000行
#df_tspro1 = ts.pro_bar(api = a.api , ts_code = '601318.sh', freq = '1min' , adj = None , start_date = a.start_date.strftime('%Y-%m-%d %H:%M:%S') , end_date = a.end_date.strftime('%Y-%m-%d %H:%M:%S') , adjfactor = True , factors = ['tor', 'vr'] , asset = 'E')
#从数据库读取
a.fq = data.复权.动态复权
a.code = '601318.sh'
a.ktype = '1d'
#a.vendor = a.vendor.tusharePro
###1. 读取tsprpo数据1
a.start_date = datetime(2000,1,1,8)
a.end_date = datetime(2022,1,1,8)
df_day1 = a.get_k_data().sort_values(by = ['date'] )
df_day1['date'] = pd.to_datetime(df_day1['date'])
print(df_day1)
###2. 保存HDF5文件1
df_day1.to_hdf(path_or_buf='.\\data\\hdf5\\demo_day.h5', mode = 'a' , append  = True , complevel  = 5 , complib  = 'blosc' , format="table" , key='test')

###3. 读取tsprpo数据2
a.start_date = datetime(2022,1,1,8)
a.end_date = datetime(2023,4,1,8)
df_day2 = a.get_k_data().sort_values(by = ['date'] )
df_day2['date'] = pd.to_datetime(df_day2['date'])
print(df_day2)
###4. 保存HDF5文件2
df_day2.to_hdf(path_or_buf='.\\data\\hdf5\\demo_day.h5', mode = 'a' , append  = True , complevel  = 5 , complib  = 'blosc' , format="table" , key='test')

###4. 读取HDF5文件
store = pd.HDFStore(path = '.\\data\\hdf5\\demo_day.h5' , key = 'test' )
#去重后再次保存
store['test']['date'] = pd.to_datetime(store['test']['date'])
store['test'].drop_duplicates(subset = ['date'] , keep = False , inplace = True)
print(store['test'])
store.close()
##df_tspro2.to_hdf()
#store = pd.HDFStore('.\\data\\hdf5\\demo.h5')

#, where=["['date'] > '2022/6/1'"]
#读取测试

store = pd.HDFStore(path = '.\\data\\hdf5\\demo_day.h5' , key = 'day' , where = ["date >= '2010/1/1'"])
store.close()
#store.select( key = '/test' , where = ["code = 601318.SH"])
print(store['day'])
print(store['test'].query('date >= "2023/1/1"'))
store = pd.read_hdf('.\\data\\hdf5\\demo.h5', key = '/test')
store.select("test", where="date >='2022/6/1'")
for key in store.keys():
    print(store[key].name)
    print(store[key].shape)
    #print(store[key].value)
#pd.HDFStore('.\\data\\hdf5\\demo.h5')
print(store)
df_h5 = store['df_tspro2']
print(df_h5)