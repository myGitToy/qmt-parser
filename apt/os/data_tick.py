# -*- coding: utf-8 -*-
from datetime import datetime,timedelta
import sqlalchemy
from jqdatasdk import *
import numpy as np
import pandas as pd
import tushare as ts
import sqlalchemy
import logging
import os
#载入基类
from apt.os.tsos import TSOS
from enum import Enum



class Data_tick(TSOS):  
    """
    数据加载类，继承自TSOS
    调用时请添加引用：from apt.os.data_tick import Data_tick
    """
    class Server(Enum):
        aliyun = 1
        localhost = 2
        nas = 3

    def __init__(self , server_name = Server.localhost):
        #初始化连接信息，这里未来计划需要迁移，因为直接把密码写入代码是不正确的
        """
        if server_name == 1:
            self.engine = sqlalchemy.create_engine('mysql+pymysql://stock_user:a@1#Yy1c@rm-uf670x8h47fdgl82tqo.mysql.rds.aliyuncs.com:3306/stock')
        elif server_name == 2:
            self.engine = sqlalchemy.create_engine('mysql+pymysql://stock_user:a@localhost:3306/stock')
        elif server_name == 3:
            self.engine = sqlalchemy.create_engine('mysql+pymysql://stock_user:a@localhost:3306/stock')            
        """
        self.engine = sqlalchemy.create_engine('mysql+pymysql://stock_user:a@1#Yy1c@localhost:3306/stock')
        auth('13817092632','JQ@tushare123')
    
    def get_tick_data(self , code = None , day = '2020-01-01'):
        day = day   #时间格式必须是YYYY-MM-DD
        code = code #code格式必须是000000，即ts传统格式，非ts pro 非jqdata代码格式，如果需要代码转换，请运行normalize_code(code)
        df = ts.get_tick_data(code , date = day , src = 'tt')   #历史分笔交易  支持ETF 基本上为每隔三秒左右生成的合并数据
        if df is None:
            return pd.DataFrame()
        else:
            df['time'] = day + ' ' + df['time']
            df['time'] = pd.to_datetime(df['time'])
            df['code'] = code
            #去除重复
            df.drop_duplicates('time', keep = 'first' , inplace = True)
            return df

    def get_last_update(self , code = None):
        """
        获取指定代码最后更新的tick数据
        返回 data YYYY-MM-DD
        """
    def daily_update(self):
        """
        tick数据的每日更新任务
        """
        ##########读取更新列表
        code_list  = list(get_all_securities(['stock','etf'],date = '2020-12-11').index)
        day_list = get_trade_days(start_date='2020-12-08', end_date='2020-12-11')
        for day in day_list:
            print("##############正在更新%s数据##############" % day.strftime("%Y-%m-%d"))
            print(datetime.now())
            for code in code_list:
                code = code[0:6]
                #检查数据库是否存在数据
                query = "select count(code) as num from ts_tick where code = '%s' and left(time,10)='%s'" % (code,day)
                df_old = pd.read_sql_query(query, self.engine)
                count = df_old.loc[0,'num']
                if count > 0 :
                    #此处存在数据，不进入更新序列，直接跳过
                    print("%s存在数据，跳过更新" % code)
                else:
                    #不存在数据，进行更新
                    df = self.get_tick_data(code = code , day = day.strftime("%Y-%m-%d"))
                    #保存至数据库
                    if df.empty == True:
                        print("%s tick数据为空，跳过上传" % (code))
                    #print(df)
                    else:
                        df.to_sql(
                                name = 'ts_tick',
                                con = self.engine,
                                index = False,
                                if_exists = 'append')
                        print("%s tick数据已上传完成" % (code))
            


