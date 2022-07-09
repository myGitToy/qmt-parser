import numpy as np
import pandas as pd
import tushare as ts
import sqlalchemy
import datetime
from jqdatasdk import *
from apt.vendor.jqdata.base import base as base
from sqlalchemy.types import NVARCHAR , Float, Integer , Date

class security(base):
    """
    专门处理security的类
    """
    def daily_update(self , type = ['stock','index','fund','etf','lof','fja','fjb']):
        """
        security日常更新
        type 证券类型，支持多选 默认为全部（目前不包含期货）
        """
        #打印标题
        print("############正在准备更新security证券代码信息###########")
        df_security = get_all_securities(type)
        #将code的索引转换成列
        df_security.reset_index(level = 0 , inplace = True)
        #重命名为code
        df_security.rename(columns = {'index':'code'} , inplace = True)
        #print(df_security)
        #dataframe列名的数据类型进行映射
        dtypedict = {
            'code': NVARCHAR(length = 24),
            'display_name': NVARCHAR(length = 128),
            'name': NVARCHAR(length = 128),
            'start_date': Date(),
            'end_date': Date(),
            'type': NVARCHAR(length = 8)
                    }
        #数据保存至数据库
        if df_security.empty == True:
            print("原始数据为空，无法导入数据库")
        else:
            df_security.to_sql(
                    name = 'jqdata_security',
                    con = self.engine,
                    index = False,
                    if_exists = 'replace',
                    index_label='code' , #设置主键(设置未成功)
                    dtype=dtypedict) #映射列的数据类型

            with self.engine.connect() as con:
                #设置主键
                con.execute('ALTER TABLE `jqdata_security` ADD PRIMARY KEY (`code`);')
                #设置索引（其实主键和索引一致的话，是可以不需要设置索引的）
                #con.execute('CREATE INDEX index `jqdata_security` (`code`);')
            print("数据已上传完成(security)")

    def get_all_code(self , day = datetime.datetime.now() , type = ['stock','etf']):
        """
        获取本地数据库中的证券代码（按日期）
        【输入】
            day 定位的日期
            type：证券类型 ['stock','index','fund','etf','lof','fja','fjb']
        """
        type_string = ','.join(["'%s'" % item for item in type ])
        sql = f"select * from jqdata_security where start_date<='{day.date()}' and end_date >='{day.date()}' and type in ({type_string})"
        df_db = pd.read_sql_query(sql , self.engine)
        if df_db.shape[0] == 0 :
            #数据库不存在数据
            return pd.DataFrame()
        else:
            #数据库存在数据，返回
            return df_db

    def get_security(self , code = None , day = datetime.datetime.now()):
        """
        获取单代码的security信息（需要满足）
        【输入】
            code 证券代码 默认为空
        【输出】
            dataframe:code|display_name|name|start_date|end_date|type|valid
        """
        if code != None:
            #脱机查询
            #定位数据库中的最后日期(这里默认使用510300进行查询)
            df = pd.read_sql_query(f"select * from jqdata_security where code = '{code}' and start_date<='{day.date()}' and end_date >='{day.date()}'" , self.engine)
            if df.empty == True:
                #数据库不存在数据
                return pd.DataFrame()
            else:
                #数据库存在数据，返回
                return df
        else:
            raise ValueError(f'证券代码不能为空，请检查')