# -*- coding: utf-8 -*-
from datetime import datetime,timedelta
import numpy as np
import pandas as pd
import tushare as ts
import sqlalchemy
import logging
import os
#载入基类
from apt.os.tsos import TSOS
class Data_Load(TSOS):
    """
    数据加载类，继承自TSOS
    调用时请添加引用：from apt.os.data_load import Data_Load
    数据加载的时间格式可以是2020/1/1 也可以是2020-01-01
    """
    def __init__(self):
        print('THIS IS IN APT.OS')
        pass
    def load_data(self , code : str , start = None , end = None , ktype = "D"):
        """
        从本地硬盘加载数据
        code: 证券代码
        start: 开始时间 可为空 默认全部读取
        end： 结束日期，可为空 默认为数据最后一天
        ktype： D/5/15/30/60 默认为日线
        
        """
        #证券代码不能为空
        if code == None: 
            print('证券代码输入无效，请检查') 
            return pd.DataFrame()
        code = code.zfill(6)
        #K线类型处理
        if ktype == "D":
            #日线数据
            file_path=(".\\data\\day\\%s.csv" % (code))
        elif ktype in ('5','15','30','60'):
            #K线数据（文本类型）
            file_path=(".\\data\\%smin\\%s.csv" % (ktype,code))
        elif ktype in (5,15,30,60):
            #K线数据（数字类型）
            file_path=(".\\data\\%dmin\\%s.csv" % (ktype,code))
        else:
            print("K线类型输入无效，请检查")
            return pd.DataFrame()
        #文件读取
        try:
            df = pd.read_csv(file_path)
        except IOError:
            print("无可用文件，请检查！")
            return pd.DataFrame()
        df['date'] = pd.to_datetime(df['date']  )
        df.set_index(['date'], inplace = True , drop = True)  
        
        return df[start : end]  #太厉害了，直接接受参数 而且日期参数随便写 2020-04-01 2020/4/1都可以
        pass
