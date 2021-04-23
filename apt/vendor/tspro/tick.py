# -*- coding: utf-8 -*-
from enum import Enum
from datetime import datetime,timedelta
from apt.vendor.jqdata.base import base as base
from jqdatasdk import *
import datetime
import sqlalchemy
import time
import os
import numpy as np
import pandas as pd
import tushare as ts

class tick(base):  
    """
    tick数据加载类，继承自JQDATA.BASE
    tick数据比较特殊，虽然属于tushare，但是主要的数据支持和数据表都归属于jqdata模块
        因此代码树划到tspro下，但继承关系隶属于jqdata.base
    """
    #def __init__(self ):
        #调用基类base的初始化，否则self.engine无定义
        #这里不能自定义初始化，否则无法设置基类base的属性，比如自定义数据库等等
        #super(tick,self).__init__()
    
    def get_tick_data(self , code = None , day = "2021-01-01"):
        day = day   #时间格式必须是YYYY-MM-DD格式
        code = code #code格式为jqdata代码格式
        df = ts.get_tick_data(code[0:6] , date = day , src = 'tt')   #历史分笔交易  支持ETF 基本上为每隔三秒左右生成的合并数据
        if df is None:
            return pd.DataFrame()
        else:
            df['time'] = day + ' ' + df['time']
            df['time'] = pd.to_datetime(df['time'])
            df['code'] = code
            #去除重复
            df.drop_duplicates('time', keep = 'first' , inplace = True)
            return df


    def daily_update(self , start_date = datetime.datetime(2020,1,1) , end_date = datetime.datetime.now()):
        """
        通过查询ts_tick_status表格，获取需要更新的代码和日期
        下载csv格式的数据至本地保存
        本模块不涉及数据上传数据库操作
        输入：
            start_date 开始日期 datetime
            end_date 结束日期 datetime 默认为当前时刻
        """
        N = 0
        ##########第一步：需要更新的数据插入数据库##########
        #self.tick_status_update(start_date = start_date)

        ##########第二步：取出需要更新的数据##########
        df_main = self.get_tick_null(start_date = start_date , end_date = end_date)
        ##########第三步：获取tick数据##########
        for row in df_main.itertuples():
            id = getattr(row, 'id')
            code = getattr(row, 'code')
            date = getattr(row, 'date')
            df = self.get_tick_data(code = code , day = date.strftime('%Y-%m-%d'))
            ##########第四步：保存csv数据##########            
            count = df.shape[0]
            if count > 0 :
                #有数据，进行CSV
                #备注 只能创建单层文件夹
                #要创建多层文件夹请使用os.makedirs
                path = f".\\data\\tick\\{date.strftime('%Y-%m-%d')}\\"
                if not os.path.exists(path):
                    os.mkdir(path)               
                df.to_csv(f"{path}{code}.csv", encoding = 'utf_8_sig')
                print(f"{date} {code} 保存完毕，共有{count}条数据 {N}")
            elif count == 0 :
                #无数据，不进行数据保存，将0写入数据库
                print(f"{date} {code} 无数据")
            ##########第五步：数据库更新##########
            query1 = f"update ts_tick_status set tick_status = {count} where id = {id}"
            N += 1
            try:
                df = pd.read_sql_query(query1, self.engine)
                #print(f"已插入{df.shape[0]}条新数据")
            except Exception as e:
                if str(e) == "This result object does not return rows. It has been closed automatically." :
                    #print("没有新数据")
                    pass
                else:
                    print(f"未知类型错误：{str(e)}")
               



    def get_tick_null(self , start_date = datetime.datetime(2021,1,1) , end_date =datetime.datetime.now()):
        """
        取出tick_status中的null数据，这是需要更新的部分
        通常这是每日更新的第二步
        """
        query = f"select * from ts_tick_status where tick_status is null and date between '{start_date.date()}' and '{end_date.date()}'order by date,code"
        try:
            df = pd.read_sql_query(query, self.engine)
            #print(f"已插入{df.shape[0]}条新数据")
        except Exception as e:
            if str(e) == "This result object does not return rows. It has been closed automatically." :
                print("没有新数据")
                return pd.DataFrame()
            else:
                print(f"未知类型错误：{str(e)}")
                return pd.DataFrame()
        print(f"获取{df.shape[0]}条新数据")
        return df

    def tick_status_update(self , start_date = datetime.datetime(2021,1,1)):
        """
        通过对比jqdata_1d表格，确定需要保存的数据，并将其保留
        通常这是每日更新的第一步
        """
        query = f"INSERT INTO ts_tick_status (ts_tick_status.code , ts_tick_status.date) select	d.code , d.date FROM jqdata_1d d WHERE d.date >= '{start_date.date()}' and NOT EXISTS (SELECT * FROM ts_tick_status tick WHERE tick.date = d.date	AND tick.CODE = d.CODE and d.date >= '{start_date.date()}')"
        try:
            df = pd.read_sql_query(query, self.engine)
            print(f"已插入{df.shape[0]}条新数据")
        except Exception as e:
            if str(e) == "This result object does not return rows. It has been closed automatically." :
                print("没有新数据")
            else:
                print(f"未知类型错误：{str(e)}")
        


    def export_to_mysql(self , df = None , code = None):
        """
        通过线程的方式写入数据库
        """
        if df.empty == True:
            print("无效的数据")
            return 0
        else:
            df.to_sql(
                        name = 'ts_tick',
                        con = self.engine,
                        index = False,
                        if_exists = 'append')
            print("%s tick数据已上传完成" % (code))

if __name__=="__main__":
    #tick2 = tick(myauth = False)
    tick = tick(rds_host = base.数据源.localhost , myauth = False)
    tick.daily_update(start_date = datetime.datetime(2021,1,1),end_date = datetime.datetime(2021,1,31))
    #tick.daily_update(start_date = datetime.datetime(2021,1,6),end_date = datetime.datetime(2021,1,9))
    #tick.get_tick_null(start_date = datetime.datetime(2021,3,1))