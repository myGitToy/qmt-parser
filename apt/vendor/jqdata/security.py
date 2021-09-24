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
            #设置主键
            with self.engine.connect() as con:
                con.execute('ALTER TABLE `jqdata_security` ADD PRIMARY KEY (`code`);')
            print("数据已上传完成(security)")