# -*- coding: utf-8 -*-
from dateutil import rrule
from datetime import datetime,date,timedelta
from apt.vendor.tspro.base import base as base
from apt.vendor.tspro.base import stock as stock
from apt.vendor.tspro.data import data as data
from apt.vendor.tspro.pro_api import pro_api
from apt.vendor.akshare.data import data as ak_data
from apt.os.minio.MinioHandler import MinioClientWrapper as MinioClient
import tushare as ts
import pandas as pd
import numpy as np
import pandas as pd
import h5py 
import os.path
import uuid
import io
class MinioHDF5Handler(data, MinioClient):
    """
    通过minio对hdf5文件的读取，加载，删除，更新的基类
    默认返回的内容是符合pd.read_hdf的格式标准的dataframe
    """
    def __init__(self , bucket_name = "hdf5" , bucket_prefix = '/akshare/data/1min/' , cache_dir =None , key = 'RawData'):
        """
        初始化参数
        param：
            bucket_name: 桶名称 例如'hdf5'
            bucket_prefix: 桶前缀 例如'/akshare/data/1min/
            cache_dir: 缓存目录 从env文件中获取或者自定义
            key: h5文件的key值 默认为'RawData'
        """
        super(data , self).__init__()  #支持多态继承，强制声明父类的init方法，注册api，用来对self.pro提供支持
        super(MinioClient , self).__init__()  #支持多态继承，强制声明父类的init方法，注册minio客户端，用来对self.client提供支持
        #全局变量定义
        #关于如何调用，请参考task449
        #https://huiqiao.visualstudio.com/MyFunds/_sprints/taskboard/MyFunds%20Team/MyFunds/2023Q1?workitem=449
        self.max_row = 8000  #单次更新的最大数据行（tspro的限制）
        self.key = key  #key值
        #self.minio_client = MinioClient(self)
        self.bucket_name = bucket_name
        self.bucket_prefix = bucket_prefix

    def data_delete(self):
        """
        【数据删除模块】
        删除hdf5文件中指定日期间的数据(代码无法运行)

        """
        raise ValueError("MinioHDF5模块目前不支持数据删除")
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

        数据查询 类似于get_k_data 【minio已测试】
        # TODO 考虑是否改名get_k_data
        param：
            code: 证券代码（由基类提供参数）
            start_date: 开始日期（由基类提供参数）
            end_date: 结束日期（由基类提供参数）
            key: h5文件的key值 默认为'RawData'
        【数据查询模块】
        查询minio文件系统中指定日期间的数据
        由于pd.read_hdf的特性，无法从内存流中读取，必须先存盘再读取
        默认返回的内容是符合pd.read_hdf的格式标准的dataframe
        说明：
            1. 目前本模块仅从H5文件中读取数据，不对mysql库的数据进行合并整合操作
            2. 未复权数据，且不含复权因子
            3. 按照时间升序排列
            4. 与get_k_data列格式有细微的差别，不含code列（未来可能会有变化）
        输出为pandas DataFrame格式
            #   Column  Non-Null Count  Dtype
            ---  ------  --------------  -----
            0   code    6 non-null      object
            1   date    6 non-null      datetime64[ns]
            2   open    6 non-null      float64
            3   close   6 non-null      float64
            4   high    6 non-null      float64
            5   low     6 non-null      float64
            6   volume  6 non-null      float64
            7   money   6 non-null      float64
        """
        # 数据存盘
        download_path = os.path.join(self.MINIO_CACHE_PATH,f"{self.code}.h5")
        minio_file_path = os.path.join(self.bucket_prefix,f"{self.code}.h5")
        if self.download_file(self.bucket_name, minio_file_path, download_path):
            # 下载成功，
            # 读取hdf5文件
            df_db = pd.read_hdf(download_path, key=self.key, where=f"date >='{self.start_date}' and date <='{self.end_date}'")
            # 对数据格式进行调整，date为时间+日期格式，其余为数值格式
            df_db = df_db.reset_index()
            df_db['date'] = pd.to_datetime(df_db['date'])
            #对时间进行排序
            df_db.sort_values(by=['date'], inplace=True, ascending=False)
            #排序后再次重置索引，生成新的 0-n 索引
            #df_db = df_db.reset_index(drop=True)          
            return df_db
        else:
            # 下载未成功
            raise ValueError(f"{self.code}下载失败")

    def data_query_by_count(self):
        """
        【minio已测试】
        查询Minio文件系统中，hdf5文件中指定日期间，每天的数据量
        一般用于数据校验，1分钟线数据，每天数据量超过241条，则表明存在重复数据，整个库就必须进行调整
        返回：DataFrame格式
            2023-03-28    239
            2023-03-29    239
            2023-03-30    239
            2023-03-31    239        
        """                              
        # 数据存盘
        download_path = os.path.join(self.MINIO_CACHE_PATH,f"{self.code}.h5")
        minio_file_path = os.path.join(self.bucket_prefix,f"{self.code}.h5")
        if self.download_file(self.bucket_name, minio_file_path, download_path):
            # 下载成功，
            # 读取hdf5文件
            df_db = pd.read_hdf(download_path, key=self.key, where=f"date >='{self.start_date}' and date <='{self.end_date}'")
            # 对数据格式进行调整，date为时间+日期格式，其余为数值格式
            df_db = df_db.reset_index()
            df_db['date'] = pd.to_datetime(df_db['date'])      
            df_db = df_db.set_index('date')
            df_db = df_db.groupby(pd.Grouper(freq='D')).size()
            return df_db
        else:
            # 下载未成功
            raise ValueError(f"{self.code}下载失败")
        

    def data_update(self):
        """
        【代码从hdf5移植，未兼容minio操作】
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
        【代码从hdf5移植，未兼容minio操作】
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
        【代码从hdf5移植，未兼容minio操作】
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
                update_end_time = datetime.now() + total_time / n * update_count
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

    def print_hdf5_structure(self , file_path):
        """
        【代码从hdf5移植，未兼容minio操作】
        读取并打印 HDF5 文件的结构,显示所有表和键值
        """
        def print_attrs(name, obj):
            # 显示组/数据集的名称和类型
            if isinstance(obj, h5py.Dataset):
                print(f"数据集: {name}")
                print(f"  形状: {obj.shape}")
                print(f"  类型: {obj.dtype}")
            elif isinstance(obj, h5py.Group): 
                print(f"组: {name}")
                
            # 显示属性
            if len(obj.attrs) > 0:
                print("  属性:")
                for key, val in obj.attrs.items():
                    print(f"    {key}: {val}")
            print()
        try:
            with h5py.File(file_path, 'r') as f:
                # 打印文件结构
                print(f"文件: {file_path}")
                print("=" * 50)
                f.visititems(print_attrs)
        except Exception as e:
            print(f"读取文件时出错: {str(e)}")


    def get_hdf5(self, bucket_name, object_name, cache_path ,key='RawData'):
        """
        【代码从hdf5移植，未兼容minio操作】
        从MinIO读取HDF5文件并转为DataFrame
        params:
            bucket_name: MinIO桶名称
            object_name: MinIO对象名称（带路径的）
            cache_path: 本地路径
            key: HDF5文件中的键
        COPILOT 代码 未经测试
        """
        # 第一步 将HDF5文件下载到本地  

        try:
            # 读取二进制内容
            content = self.read_file(bucket_name, object_name, encoding=None)
            
            # 使用BytesIO将二进制内容转换为文件对象
            with io.BytesIO(content) as bio:
                return pd.read_hdf(bio, key=key)
        except Exception as e:
            print(f"Error reading HDF5 file: {e}")
            raise
    def update_hdf5(self, df, bucket_name, object_name, key='RawData'):
        """
        【代码从hdf5移植，未兼容minio操作】
        更新DataFrame并上传到MinIO
        COPILOT 代码 未经测试
        """
        try:
            # 将DataFrame保存为HDF5格式的二进制内容
            bio = io.BytesIO()
            df.to_hdf(bio, key=key, mode='w')
            bio.seek(0)
            
            # 上传到MinIO
            self.minio_client.client.put_object(
                bucket_name,
                object_name,
                bio,
                bio.getbuffer().nbytes
            )
        except Exception as e:
            print(f"Error updating HDF5 file: {e}")
            raise

if __name__ == '__main__':
    a = MinioHDF5Handler()
    print(a.MINIO_CACHE_PATH)
    a.start_date = datetime(2020,1,7,9,0)
    a.end_date = datetime(2025,1,7,10,30)    
    a.code = '000001.SZ'
    a.ktype = '1m'
    # 测试文件结构
    file_structure = a.print_hdf5_structure(os.path.join(a.MINIO_CACHE_PATH,'000002.SZ.h5'))
    print(file_structure)
    db = a.data_query_by_count()

    print(db)
    file = a.read_hdf5('hdf5', 'akshare/data/1min/000002.SZ.h5')
    print(file)
    c = ak_data()   #初始化ak_data类，从a模块获取类的属性数据

    ####读取并打印 HDF5 文件的结构
    #a.file_path = "C:\\Data\\hdf5\\1min"
    #file_name = "000002.SZ.h5"
    #stream = a.print_hdf5_structure(f"{a.file_path}\\{file_name}")
    #print(stream)

    ####展示ak_data的分时线数据获取
    #df_ak = ak_data.get_k_data(a)
    #print(df_ak)

    ####展示tspro_data的分时线数据获取
    df_tspro = data.get_k_data(a)
    print(df_tspro)
    #打印df结构
    print(df_tspro.info())
    #     
    #df = a.data_query()

    #print(df)

    ####展示从本地HDF5文件中读取数据
    #a.file_path = "C:\\hdf5\\1min"  #DELL XPS15 文件目录
    a.file_path = "C:\\Data\\hdf5\\1min"  #185远程windows 文件目录


    df = a.data_query()
    print(df.columns)    
    print(df.sort_values(by='date'))
    print(df.info())
    #更新数据模块
    #a.update_sequence_add()
    #a.update_sequence_launch()
    