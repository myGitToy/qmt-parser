# -*- coding: utf-8 -*-
from dateutil import rrule
from datetime import datetime,date,timedelta
from apt.vendor.tspro.base import base as base
from apt.vendor.tspro.base import stock as stock
from apt.vendor.tspro.data import data as data
from apt.vendor.tspro.pro_api import pro_api
import tushare as ts
import pandas as pd
import numpy as np
import pandas as pd
import h5py
import os.path
import uuid
class hdf5(data):
    """
    hdf5文件的读取，加载，删除，更新的基类
    """
    def __init__(self , key = 'RawData'):
        #全局变量定义
        #关于如何调用，请参考task449
        #https://huiqiao.visualstudio.com/MyFunds/_sprints/taskboard/MyFunds%20Team/MyFunds/2023Q1?workitem=449
        self.file_path = "C:\\Data\\hdf5\\1min"  #数据存盘的根目录
        self.update_path = "C:\\Data\\hdf5" #更新列表的存盘目录（用于记录需要更新的数据）
        self.max_row = 8000  #单次更新的最大数据行（tspro的限制）
        self.key = key
        super(data , self).__init__()  #支持多态继承，强制声明父类的init方法，注册api，用来对self.pro提供支持
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
        return df_db
        print(df_db)

    def data_query_by_count(self):
        """
        查询hdf5文件中指定日期间，每天的数据量
        一般用于数据校验，1分钟线数据，每天数据量超过241条，则表明存在重复数据，整个库就必须进行调整
        """
        df_db = pd.read_hdf(f'{self.file_path}\\{self.code}.h5', key = self.key , where = f"date >='{self.start_date}' and date <='{self.end_date}'")
        print(df_db.groupby(pd.Grouper(level = 'date', freq = 'D')).size())

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
            df = ts.pro_bar(ts_code = self.code , freq = '1min' , adj = None , start_date = dt.strftime('%Y-%m-%d %H:%M:%S') , end_date = tmp_end_date.strftime('%Y-%m-%d %H:%M:%S') , adjfactor = True , factors = ['tor', 'vr'] , asset = 'E')
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
            df_add.to_hdf(path_or_buf=f'{self.file_path}\\{self.code}.h5', mode = 'a' , append  = True , complevel  = 5 , complib  = 'blosc' , format = "table" , key = self.key)
            #输出数量
            print(f'{self.code} 1分钟线更新完毕，添加{df_add.shape[0]}条数据；')
        else:
            print(f'{self.code} 区间内无新增数据；')
    def update_sequence_add(self , code_list = None , myclass = 'stock' , type = '60m'  , priority = 0 ):
        '''
        task346更改了分时线数据更新的逻辑，拆分成add和launch两部分
        H5 DataFrame格式如下：
        uuid|code|start_date|end_date|type|priority
        uuid（索引）|证券代码|开始日期|结束日期|更新数据的类型 如1min|是否优先更新
        add模块主要进行数据更新任务的导入
        输入：
            code_list 需要更新的证券代码列表，有列表（优先更新）和无列表（正常更新）进入的是两个不同的流程
            myclass 一级目录 默认stock  目前可接受参数stock|etf
            type 二级目录 默认60m；目前可接受参数：60m/1m
            priority 优先更新标识 默认为0
        '''
        #####更新证券列表######
        code_list = pro_api.stock_basic(self)[['code','name']]
        code_list['uuid'] = code_list.apply(lambda _: str(uuid.uuid1()).replace('-', ''), axis=1)
        #备注：在生成uuid过程中，不能包含- 否则在保存时会报错
        code_list['class'] = myclass
        code_list['type'] = type
        code_list['priority'] = priority
        code_list['start_date'] = self.start_date
        code_list['end_date'] = self.end_date
        pd.set_option('display.max_columns', None)
        #print(code_list)
        #####END######

        ######检查H5文件######
        full_path = f'{self.update_path}\\update_sequence.h5'
        df_db = pd.DataFrame()
        if os.path.exists(full_path):
            #文件存在，读取本地文件
            df_db = pd.read_hdf(full_path , key = self.key )
            #返回真实行数
            df_db_count = df_db.shape[0]
        else:
            #文件不存在，直接返回行数0
            df_db_count = 0
        print(f'H5文件中目前存在{df_db_count}条记录')
        if df_db_count == 0:
            #H5文件不存在数据，直接添加
            #with h5py.File(full_path, 'w') as f:
                # Create a new dataset
                #dset = f.create_dataset(f'/{self.key}', data = code_list)
            code_list.to_hdf(path_or_buf = full_path, mode = 'w' , append  = True , complevel  = 5 , complib  = 'blosc' , format = "table" , key = self.key)
            print(f"已新建{code_list.shape[0]}条记录，时间范围{self.start_date.date()}-{self.end_date.date()}")
        else:
            #H5文件存在数据，进行选择
            result = input('''H5存在数据，请选择更新方式 \n
            1. 保留原有更新序列，添加新的序列 \n
            2. 删除原有更新序列，添加新的序列 \n
            3. 删除原有更新序列 \n
            4. 退出（不做任何处理）\n''')
        #print(data.token)
        #print(pro_api.stock_basic(self))
            if result == '1' :
                #追加数据
                code_list.to_hdf(path_or_buf = full_path, mode = 'a' , append  = True , complevel  = 5 , complib  = 'blosc' , format = "table" , key = self.key)
                print(f"已追加{code_list.shape[0]}条记录，时间范围{self.start_date.date()}-{self.end_date.date()}")
            elif result == '2':
                #写入
                code_list.to_hdf(path_or_buf = full_path, mode = 'w' , append  = True , complevel  = 5 , complib  = 'blosc' , format = "table" , key = self.key)
                print(f"已新建{code_list.shape[0]}条记录，时间范围{self.start_date.date()}-{self.end_date.date()}")
            elif result == '3':
                #删除
                #目前这边还有一些bug，在删除dataset后，重新读取会出现以下错误
                #'No object named RawData in the file'
                #所以最好的解决方法是直接删除文件
                with pd.HDFStore(full_path, 'a') as store:
                    if f'/{self.key}' in store:
                        store.remove(f'/{self.key}')
            elif result == '4':
                pass
            else:
                pass

    def update_sequence_launch(self , priority = 0 ):
        '''
        task346更改了分时线数据更新的逻辑，拆分成add和launch两部分
        launch模块主要进行数据更新任务，支持点断续传
        priority 是否优先更新 默认为0 目前H5文件在priority不写入索引的情况下，无法做到区分是否优先更新
        【bug report】end_date的设置一定要小心
        如果当前日期是3/21，那如果end_date选择3/20，则取出比较和去重的数据是3/20，但实际数据库里含有3/21的数据
        但是用3/20的数据去更新，实际又会更新到21号的数据
        因此在当前逻辑下会重复更新3/21号的数据
        这个bug连带出来还有一个问题就是必须顺序更新，不能更新2023年以后再更新前面的，会出错
        '''
        #读取全部数据
        full_path = f'{self.update_path}\\update_sequence.h5'
        df_sequence = pd.read_hdf(full_path, key = self.key )
        #初始化token（这里其实不需要dell XPS15能正常运行，迁移到R730就需要重新设置TOKEN）
        ts.set_token(self.token)
        #查看需要更新的列表
        #print(df_sequence)
        code_list = df_sequence['code']
        if df_sequence.shape[0] > 0 :
            #有数据，进行更新
            #设定最大更新行数
            max_row = self.max_row
            #设定总更新数据
            update_count = df_sequence.shape[0]
            #设定当前更新进读
            n = 1
            #设定更新开始时间
            update_start_time = datetime.now()
            for index , row in df_sequence.iterrows():
                id = row['uuid']
                code = row['code']
                #start_date = datetime.strftime(row['start_date'] , '%Y-%m-%d')
                #end_date  = datetime.strftime(row['end_date'] , '%Y-%m-%d')
                start_date = row['start_date']
                end_date  = row['end_date']
                myclass = row['class']
                type = row['type']
                #######tushare PRO数据更新模块
                #tspro pro_bar数据获取模块
                df_tspro = pd.DataFrame()
                for dt in rrule.rrule(rrule.MONTHLY, dtstart = start_date, until = end_date):    
                    #print(dt.strftime("%Y-%m") )
                    #print(f"时间范围：{dt} - {dt  + timedelta(days = 35)}")
                    tmp_end_date = dt  + timedelta(days = 35)
                    #####1.1 从tspro取出时间段内的所有数据（需要做很多变形处理才能适配数据规范）
                    df = ts.pro_bar( ts_code = code , freq = '1min' , adj = None , start_date = dt.strftime('%Y-%m-%d %H:%M:%S') , end_date = tmp_end_date.strftime('%Y-%m-%d %H:%M:%S') , adjfactor = True , factors = ['tor', 'vr'] , asset = 'E')
                    #df = ts.pro_bar( ts_code = '601318.sh' , freq = '1min' , adj = None , start_date = '2022-09-01 09:00:00' , end_date = '2022-10-01 16:00:00' , adjfactor = True , factors = ['tor', 'vr'] , asset = 'E')
                    #最大数据量校验（此处保留校验，本模块做了月度更新处理，理论上不会触发超8000行）
                    if df.shape[0] >= max_row:
                        raise ValueError(f'接收到的数据达到最大允许值，可能存在数据丢失，中止更新！')
                    df_tspro = pd.concat([df_tspro , df] , axis = 0 ) 
                    #print('-----')    
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
                #根据需要更新的数据区间进行筛选，tspro仅返回区间内的数据，以免造成重复更新
                #print(df_tspro)
                #print(df_tspro.query("date >= @start_date & date <= @end_date"))
                df_tspro = df_tspro.query("date >= @start_date & date <= @end_date")
                #以上 tspro数据更新模块完成

                #########临时模块：将数据写入HDF5文件#########
                #目的是一次性写入，因为测试文件可能并不存在，需要这个模块创建测试文件
                #df_tspro.to_hdf(path_or_buf=f'{file_path}\\{a.code}.h5', mode = 'w' , append  = True , complevel  = 5 , complib  = 'blosc' , format="table" , key='test')
                #########临时模块END#########

                ###2. 读取H5文件（指定日期间的数据）
                #计算更新耗时
                total_time = datetime.now() - update_start_time\
                #计算更新结束时间
                update_end_time = datetime.now() + total_time / n * (update_count - n)
                file_path_h5 = f'{self.file_path}\\{code}.h5'
                df_db = pd.DataFrame()
                if os.path.exists(file_path_h5):
                    #文件存在，读取本地文件（读取文件的区间与tspro数据更新的区间保持一致）
                    df_db = pd.read_hdf(file_path_h5, key = self.key , where = f"date >='{start_date}' and date <='{end_date}'")
                #print(df_db)
                #列出原始数据的行数，进行筛查有没有重复的日期
                #print(df_db.groupby(pd.Grouper(level='date', freq='D')).size())
                ###3. 检查两个版本的差集
                df_add = pd.concat([df_tspro , df_db , df_db ]).drop_duplicates( keep = False)
                #print(df_add)

                ###4. 追加保存HDF5文件
                if df_add.shape[0] >0 :
                    #有数据，则差集写入H5
                    df_add.to_hdf(path_or_buf = file_path_h5 , mode = 'a' , append  = True , complevel  = 5 , complib  = 'blosc' , format="table" , key = self.key)
                    print(f'{n}/{update_count} 已更新{code}，时间范围{start_date.date()}-{end_date.date()}，总写入数据量{df_add.shape[0]}|预计更新完成时间{update_end_time};')
                else:
                    #无数据 跳过更新
                    print(f'{n}/{update_count} {code}无数据，跳过更新;')
                ###5. 数据已更新，删除该条UUID的更新请求
                #目前实现方法是重新打开数据->读取全部记录->删除特定uuid的记录->写回文件
                df_store = pd.read_hdf(full_path, key = self.key)
                df_store = df_store[df_store['uuid'] != id]
                df_store.to_hdf(path_or_buf = full_path , mode = 'w' , append  = True , complevel  = 5 , complib  = 'blosc' , format = "table" , key = self.key)
                #进读+1
                n = n + 1
if __name__ == '__main__':
    #2014年数据 2600条 全部更新完毕约7小时
    #2022年数据已更新完毕
    a = hdf5()
    a.start_date = datetime(2023,1,1,8)
    a.end_date = datetime(2023,3,31,16)    #正在更新2023Q1数据
    a.code = '000001.SZ'
    a.ktype = '1min'
    #df = a.data_query()
    #print(df)
    a.update_sequence_add()
    a.update_sequence_launch()
    