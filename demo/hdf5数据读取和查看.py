from datetime import datetime
import tushare as ts
import pandas as pd
from apt.vendor.tspro.data import data
pd.set_option('display.max_columns', None)
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
#读取文件
#store = pd.HDFStore(path = '.\\data\\\\demo_day.h5' , key = '/day' )
store = pd.read_hdf('.\\data\\\\demo_day_index_test.h5', key = 'test' , where = "date >'2020/1/1'")
for key in store.keys():
    print(store[key].name)
    print(store[key].shape)
#逆运算，将索引重新转换成列
store.reset_index(inplace = True )
print(store)

#去重后重新保存
#store['date'] = pd.to_datetime(store['date'])      #实际测试下来，date的[NS64]化不需要，但是为了逻辑的完整性，这里予以保留
store.drop_duplicates(subset = ['date'] , keep = 'first' , inplace = True)  #keep = False 实际起到了去重的作用
store = store.set_index(['code','date'] , drop = True)
print(store)
store.to_hdf(path_or_buf='.\\data\\\\demo_day.h5', mode = 'w' , append  = True , complevel  = 5 , complib  = 'blosc' , format="table" , key='test')


