# -*- coding: utf-8 -*-
from enum import Enum
from datetime import datetime,timedelta
from apt.vendor.jqdata.base import base as base
from jqdatasdk import *
import datetime
import sqlalchemy
import time
import numpy as np
import pandas as pd
import tushare as ts

class tick(base):  
    """
    tick数据加载类，继承自JQDATA.BASE
    tick数据比较特殊，虽然属于tushare，但是主要的数据支持和数据表都归属于jqdata模块
        因此代码树划到tspro下，但继承关系隶属于jqdata.base
    调用时请添加引用：from apt.os.data_tick import Data_tick
    """
    #def __init__(self ):
        #调用基类base的初始化，否则self.engine无定义
        #这里不能自定义初始化，否则无法设置基类base的属性，比如自定义数据库等等
        #super(tick,self).__init__()
    
    def get_tick_data(self , code = None , day = '2020-01-01'):
        day = day   #时间格式必须是YYYY-MM-DD
        code = code #code格式为jqdata代码格式
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
    def daily_update(self , start_date = datetime.datetime(2020,1,1) , end_date = datetime.datetime.now()):
        """
        通过查询ts_tick_status表格，获取需要更新的代码和日期
        下载csv格式的数据至本地保存
        本模块不涉及数据上传数据库操作
        输入：
            start_date 开始日期 datetime
            end_date 结束日期 datetime 默认为当前时刻
        """
        ##########读取更新列表
        query2 = ""
        df_list =  ""
        code_list  = list(get_all_securities(['stock','etf'],date = end_date.date).index)
        day_list = get_trade_days(start_date = start_date, end_date = end_date)
        for day in day_list:
            print("##############正在更新%s数据##############" % day.strftime("%Y-%m-%d"))
            print(datetime.datetime.now())
            for code in code_list:
                code = code[0:6]
                #检查数据库是否存在数据
                query = "select count(code) as num from ts_tick where code = '%s' and date(time)='%s'" % (code,day)
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
                        time1 = datetime.datetime.now()
                        df.to_sql(
                                name = 'ts_tick',
                                con = self.engine,
                                index = False,
                                if_exists = 'append')
                        time2 = datetime.datetime.now()
                        print("%s tick数据已上传完成，耗时%s" % (code,(time2-time1)))

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
        

    def update_v2(self , start_date = datetime.datetime(2020,1,1) , end_date = datetime.datetime.now()):
        """
        tick数据的每日更新任务
        按代码循环，再获取每天的数据，一次性写入，希望能提高运行效率
        输入：
            start_date 开始日期 datetime
            end_date 结束日期 datetime 默认为当前时刻
        """
        ##########读取更新列表
        code_list  = list(get_all_securities(['stock','etf'],date = end_date.date).index)
        day_list = get_trade_days(start_date = start_date, end_date = end_date)
        for code in code_list:
            #print("##############正在更新%s数据##############" % day.strftime("%Y-%m-%d"))
            #print(datetime.datetime.now())
            code = code[0:6]
            #定义主df 目前此位置为空
            df_main = pd.DataFrame()
            for day in day_list:
                
                #检查数据库是否存在数据
                query = "select count(code) as num from ts_tick where code = '%s' and date(time)='%s'" % (code,day)
                df_old = pd.read_sql_query(query, self.engine)
                count = df_old.loc[0,'num']
                if count > 0 :
                    #此处存在数据，不进入更新序列，直接跳过
                    pass
                    #print("%s存在数据，跳过更新" % day.strftime("%Y-%m-%d"))
                else:
                    #不存在数据，进行更新
                    df = self.get_tick_data(code = code , day = day.strftime("%Y-%m-%d"))
                    #添加进队列
                    df_main = df_main.append(df)
                    #print(df_main)
            #保存至数据库
            if df_main.empty == True:
                print("%s tick数据为空，跳过上传" % (code))
            #print(df)
            else:
                #print( df_main.loc[0,'time'])
                """
                这里结果挺奇怪的
                0   2020-12-17 09:25:00
                0   2020-12-18 09:25:01
                0   2020-12-21 09:25:01
                0   2020-12-22 09:25:01
                0   2020-12-23 09:25:01
                0   2020-12-24 09:25:01
                0   2020-12-25 09:25:00
                """
                time1 = datetime.datetime.now()
                df_main.to_sql(
                        name = 'ts_tick',
                        con = self.engine,
                        index = False,
                        if_exists = 'append')
                time2 = datetime.datetime.now()
                print("%s tick数据已上传完成，耗时%s" % (code,(time2-time1)))
                #print("%s tick数据已上传完成 %s - %s" % (code , df_main.head(1).loc[0,'time'].strftime("%Y-%m-%d") , df_main.tail(1).loc[0,'time'].strftime("%Y-%m-%d")))

    def update_t1(self , start_date = datetime.datetime(2020,1,1) , end_date = datetime.datetime.now()):
            """
            tick数据的每日更新任务（线程写入版）
            单日单代码循环 效率较低
            输入：
                start_date 开始日期 datetime
                end_date 结束日期 datetime 默认为当前时刻
            """
            ##########读取更新列表
            code_list  = list(get_all_securities(['stock','etf'],date = end_date.date).index)
            day_list = get_trade_days(start_date = start_date, end_date = end_date)
            for day in day_list:
                print("##############正在更新%s数据##############" % day.strftime("%Y-%m-%d"))
                print(datetime.datetime.now())
                for code in code_list:
                    code = code[0:6]
                    #检查数据库是否存在数据
                    query = "select count(code) as num from ts_tick where code = '%s' and date(time)='%s'" % (code,day)
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
                            #需要更新，进行线程写入
                            t = threading.Thread(target = self.export_to_mysql(df = df , code = code) , name = 'Exporting')
                            t.start()
                            t.join()


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
    tick.tick_status_update()