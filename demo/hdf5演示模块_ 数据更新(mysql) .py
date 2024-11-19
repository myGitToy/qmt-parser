"""
目的：
测试H5文件用于证券数据更新
1. 从H5文件中读取更新日期起止时间段的数据
2. 从mysql中读取更新日期起止时间段的数据
3. 数据去重处理后重新写入H5文件
4. mysql中对应的数据删除（1min线）
备注：
1. 演示模块的数据周期为1分钟线，保存位置为C:\\hdf5\1min
2. 数据为不包含factor的不复权数据
3. 数据保存格式：code和date作为index写入H5文件

"""
from dateutil import rrule  #mysql版本不需要按月进行历遍，直接读取指定日期段的数据（tspro有最大8000条的限制，因此才需要）
from datetime import datetime,date,timedelta
from apt.vendor.akshare.data import data as ak_data
import h5py
import tushare as ts
import pandas as pd
from apt.os.hdf5 import hdf5 as hdf5

#全局变量定义
file_path = "C:\\Data\\hdf5\\1min"  #数据存盘的根目录
max_row = 8000  #单次更新的最大数据行（tspro的限制）
df_ak = pd.DataFrame() #ak主数据
a = ak_data()
nw = datetime.now()
a.start_date = datetime(2023,3,12,8)
a.end_date = datetime(2024,3,20,16)
a.fq = ak_data.复权.动态复权
a.code = '601318.sh'
a.ktype = '1m'

#####1.1 从mysql中取出时间段内的所有数据（
#df = ts.pro_bar(api = a.api , ts_code = a.code , freq = '1min' , adj = None , start_date = dt.strftime('%Y-%m-%d %H:%M:%S') , end_date = tmp_end_date.strftime('%Y-%m-%d %H:%M:%S') , adjfactor = True , factors = ['tor', 'vr'] , asset = 'E')
df = a.get_k_data() #从数据库中读取数据
print(df)
df_h5 = hdf5(a).data_query()
print(df_h5)
#df = ts.pro_bar( ts_code = '601318.sh' , freq = '1min' , adj = None , start_date = '2022-09-01 09:00:00' , end_date = '2022-10-01 16:00:00' , adjfactor = True , factors = ['tor', 'vr'] , asset = 'E')
#最大数据量校验（此处保留校验，本模块做了月度更新处理，理论上不会触发超8000行）
if df.shape[0] >= max_row:
    raise ValueError(f'接收到的数据达到最大允许值，可能存在数据丢失，中止更新！')
df_tspro = pd.concat([df_tspro , df] , axis = 0 ) 
print('-----')    
#####1.2 tspro数据读取完毕，进行变形处理和适配
df_tspro.rename(columns={"ts_code": "code", "trade_time": "date" ,"vol" : "volume" , "amount" : "money"} , errors="raise" , inplace = True)
df_tspro.drop(columns = ['trade_date','pre_close'] , inplace = True)
#时间日期类的列进行类型变更
df_tspro['date'] = pd.to_datetime(df_tspro['date'])
#日期排序(目前判定下为非必要，预留代码，减小数据更新的压力)
df_tspro.sort_values(by = ['date'], inplace = True , ascending = False)
#分时线数据不需要进行成交量和成交额修正
df_tspro.drop_duplicates(subset = ['code', 'date'], keep = 'first', inplace = True)
#code date进行索引化
df_tspro = df_tspro.set_index(['code','date'] , drop = True)
print(df_tspro)
#以上 tspro数据更新模块完成

#########临时模块：将数据写入HDF5文件#########
#目的是一次性写入，因为测试文件可能并不存在，需要这个模块创建测试文件
#df_tspro.to_hdf(path_or_buf=f'{file_path}\\{a.code}.h5', mode = 'w' , append  = True , complevel  = 5 , complib  = 'blosc' , format="table" , key='test')
#########临时模块END#########

###2. 读取H5文件（指定日期间的数据）
full_path = f'{self.file_path}\\{self.code}.h5'
df_db = pd.DataFrame()
if os.path.exists(full_path):
    #文件存在，读取本地文件
    df_db = pd.read_hdf(full_path, key = self.key , where = f"date >='{self.start_date}' and date <='{self.end_date}'")
print(df_db)
#列出原始数据的行数，进行筛查有没有重复的日期
print(df_db.groupby(pd.Grouper(level='date', freq='D')).size())
###3. 检查两个版本的差集
df_add = pd.concat([df_tspro , df_db , df_db ]).drop_duplicates( keep = False)
print(df_add)

###4. 追加保存HDF5文件
df_add.to_hdf(path_or_buf=f'{file_path}\\{a.code}.h5', mode = 'a' , append  = True , complevel  = 5 , complib  = 'blosc' , format="table" , key='test')

