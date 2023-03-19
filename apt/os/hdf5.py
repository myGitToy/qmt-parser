# -*- coding: utf-8 -*-
from dateutil import rrule
from datetime import datetime,date,timedelta
from apt.vendor.tspro.data import data
import tushare as ts
import pandas as pd
import numpy as np
import pandas as pd
import h5py
import os.path
class hdf5(data):
    """
    hdf5文件的读取，加载，删除，更新的基类
    """
    def __init__(self , key = 'RawData'):
        #全局变量定义
        self.file_path = "C:\\Data\\hdf5\\1min"  #数据存盘的根目录
        self.max_row = 8000  #单次更新的最大数据行（tspro的限制）
        self.key = key

    def data_delete(self):
        """
        删除hdf5文件中指定日期间的数据(代码无法运行)

        """
        df = pd.read_hdf('test.h5', 'test')
        df = df.loc['2022-01-01':'2022-12-31']
        df.to_hdf('test.h5', 'test')
        """
        with h5py.File(f'{self.file_path}\\{self.code}.h5', 'r+') as f:
            # 获取/test下的数据集
            dset = f['/test']
            # 获取2022/1/1到2023/1/1期间的数据
            dt = dset['2023/3/17':'2023/3/18']
            print(dt)
            #dt = dset[self.start_date:self.end_date]
            # 删除数据
            dset = np.delete(dset, dt, axis=0)
        """
    def data_query(self):
        """
        查询hdf5文件中指定日期间的数据
        输出为pandas DataFrame格式
        """
        df_db = pd.read_hdf(f'{self.file_path}\\{self.code}.h5', key = self.key , where = f"date >='{self.start_date}' and date <='{self.end_date}'")
        print(df_db)

    def data_query_by_count(self):
        """
        查询hdf5文件中指定日期间，每天的数据量
        一般用于数据校验，1分钟线数据，每天数据量超过241条，则表明存在重复数据，整个库就必须进行调整
        """
        df_db = pd.read_hdf(f'{self.file_path}\\{self.code}.h5', key = self.key , where = f"date >='{self.start_date}' and date <='{self.end_date}'")
        print(df_db.groupby(pd.Grouper(level='date', freq='D')).size())

    def data_update(self):
        """
        更新指定日期间的所有数据（目前只支持1分钟线）
        遵循 API数据读取->H5数据读取->差集更新->写回文件 的顺序
        重要提示：本模块的更新为临时存在，hdf5模块为OS类操作，未来会将数据更新模块移走
        """
        #1分钟线校验
        df_tspro = pd.DataFrame()
        if self.ktype != '1min':
            raise ValueError(f'目前只允许对1分钟线进行更新')
        for dt in rrule.rrule(rrule.MONTHLY, dtstart = self.start_date, until = self.end_date):    
            #print(dt.strftime("%Y-%m") )
            #print(f"时间范围：{dt} - {dt  + timedelta(days = 35)}")
            tmp_end_date = dt  + timedelta(days = 35)
            #####1.1 从tspro取出时间段内的所有数据（需要做很多变形处理才能适配数据规范）
            df = ts.pro_bar( ts_code = self.code , freq = '1min' , adj = None , start_date = dt.strftime('%Y-%m-%d %H:%M:%S') , end_date = tmp_end_date.strftime('%Y-%m-%d %H:%M:%S') , adjfactor = True , factors = ['tor', 'vr'] , asset = 'E')
            #df = ts.pro_bar( ts_code = '601318.sh' , freq = '1min' , adj = None , start_date = '2022-09-01 09:00:00' , end_date = '2022-10-01 16:00:00' , adjfactor = True , factors = ['tor', 'vr'] , asset = 'E')
            #最大数据量校验（此处保留校验，本模块做了月度更新处理，理论上不会触发超8000行）
            if df.shape[0] >= self.max_row:
                raise ValueError(f'接收到的数据达到最大允许值，可能存在数据丢失，中止更新！')
            df_tspro = pd.concat([df_tspro , df] , axis = 0 ) 
            #print('-----')    
        #####1.2 tspro数据读取完毕，进行变形处理和适配
        df_tspro.rename(columns={"ts_code": "code", "trade_time": "date" ,"vol" : "volume" , "amount" : "money"} , errors = "raise" , inplace = True)
        df_tspro.drop(columns = ['trade_date','pre_close'] , inplace = True)
        #时间日期类的列进行类型变更
        df_tspro['date'] = pd.to_datetime(df_tspro['date'])
        #日期排序(目前判定下为非必要，预留代码，减小数据更新的压力)
        df_tspro.sort_values(by = ['date'], inplace = True , ascending = False)
        #分时线数据不需要进行成交量和成交额修正
        df_tspro.drop_duplicates(subset = ['code', 'date'], keep = 'first', inplace = True)
        #code date进行索引化
        df_tspro = df_tspro.set_index(['code','date'] , drop = True)
        #print(df_tspro)
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
        #print(df_db)
        ###3. 检查两个版本的差集
        df_add = pd.concat([df_tspro , df_db , df_db ]).drop_duplicates( keep = False)
        #print(df_add)


        ###4. 追加保存HDF5文件
        if df_add.shape[0] > 0 :
            #保存文件
            df_add.to_hdf(path_or_buf=f'{self.file_path}\\{self.code}.h5', mode = 'a' , append  = True , complevel  = 5 , complib  = 'blosc' , format = "table" , key =self.key)
            #输出数量
            print(f'{self.code} 1分钟线更新完毕，添加{df_add.shape[0]}条数据；')
        else:
            print(f'{self.code} 区间内无新增数据；')
if __name__ == '__main__':
    a = hdf5()
    a.start_date = datetime(2023,1,1,8)
    a.end_date = datetime(2023,3,20,16)
    a.code = '001201.SZ'
    a.ktype = '1min'
    a.data_update()
    a.data_query_by_count()