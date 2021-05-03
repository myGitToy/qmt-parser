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


    def daily_update(self , start_date = datetime.datetime(2021,1,1) , end_date = datetime.datetime.now()):
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
        self.tick_status_update(start_date = start_date)

        ##########第二步：取出需要更新的数据##########
        df_main = self.get_tick_null(start_date = start_date , end_date = end_date)
        if df_main.shape[0] == 0 :
            print(f"没有数据需要更新，程序退出")
            return 
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
        query = f"select * from ts_tick_status where tick_status is null and date between '{start_date.date()}' and '{end_date.date()}' order by date,code"
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
        print(f"{df.shape[0]}条数据需要更新")
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
                #print(f"已插入{df.shape[0]}条新数据")
                pass
            else:
                print(f"未知类型错误：{str(e)}")
        #删除指数数据
        sql = "DELETE from ts_tick_status where code in ('000001.XSHG','000002.XSHG','000003.XSHG','000004.XSHG','000005.XSHG','000006.XSHG','000007.XSHG','000008.XSHG','000009.XSHG','000016.XSHG','000010.XSHG','000300.XSHG','000688.XSHG','000905.XSHG','000852.XSHG','399001.XSHE','399005.XSHE','399006.XSHE')"
        try:
            df2 = pd.read_sql_query(sql, self.engine)
        except Exception as e:
            pass

    def mysql_to_csv(self , table_name = 'ts_tick'):     
        """
        将数据库中的数据转成csv格式
        一次性函数，随着数据库清空，此函数将被停止使用
        """
        sql_1 = f"select code,date(time) as date from {table_name} where date(time) >= '2020/10/1' group by code,date(time)"
        df_main = pd.read_sql_query(sql_1, self.engine)
        for row in df_main.itertuples():
            code = getattr(row, 'code')
            date = getattr(row, 'date')
            code_jqdata = normalize_code(code)
            #判断路径中是否存在相关数据
            t = os.path.exists(f".\\data\\tick\\{date}\\{code_jqdata}.csv")
            if t == True:
                #存在数据，直接进行删除操作
                try:
                    sql_d = f"""
                        delete from {table_name} where code = '{code}' and date(time) = '{date}';
                        
                    """
                    df = pd.read_sql_query( sql_d , self.engine)
                except:
                    print(f"{date} {code} 已删除")
            else:
                #不存在数据
                #读取并写入数据
                sql_2 = f"select time,price,`change`,volume,amount,type,`code` from {table_name} where code = '{code}' and date(time) = '{date}'"
                df = pd.read_sql_query(sql_2 , self.engine)
                df['code'] = code_jqdata
                path = f".\\data\\tick\\{date.strftime('%Y-%m-%d')}\\"
                if not os.path.exists(path):
                    os.mkdir(path)               
                df[['time','price','change','volume','amount','type','code']].to_csv(f"{path}{code_jqdata}.csv", encoding = 'utf_8_sig')
                count = df.shape[0]
                #print(f"{date} {code} 保存完毕")
                #删除数据库数据并更新tick_status的对应日期和代码的数量
                try:
                    sql_d = f"""
                        delete from {table_name} where code = '{code}' and date(time) = '{date}';
                        update ts_tick_status set tick_status = {count} where code = '{code}' and date = '{date}';
                        """
                    df = pd.read_sql_query( sql_d , self.engine)                     
                except:
                    print(f"{date} {code} 已保存并删除") 
                    
    def tick数量校验(self,start_date = datetime.datetime(2021,1,1),end_date = datetime.datetime(2021,12,31)):
        """
        用于数据库导出函数mysql_to_csv处理完毕后重新刷新下数据
        一次性函数
        """
        sql_1 = f"select code,date,tick_status from ts_tick_status where tick_status = 0 and date between '{start_date.date()}' and '{end_date.date()}'"
        df_main = pd.read_sql_query(sql_1, self.engine)
        for row in df_main.itertuples():
            code = getattr(row, 'code')
            date = getattr(row, 'date')
            #判断路径中是否存在相关数据
            t = os.path.exists(f".\\data\\tick\\{date}\\{code}.csv")
            if t == True:
                #存在文件但数量显示0 ，因此不是合理的数量，需要更新
                #加载文件并计算数量
                df = pd.read_csv(f".\\data\\tick\\{date}\\{code}.csv")
                count = df.shape[0]
                try:
                    sql_update = f"update ts_tick_status set tick_status = {count} where code = '{code}' and date = '{date}'"
                    pd.read_sql_query(sql_update, self.engine)
                except:
                    print(f"{date} {code} 数量已更新至{count}")

    def mysql_to_csv_V2(self , table_name = 'ts_tick' , start_date = None , end_date = None):     
        """
        将数据库中的数据转成csv格式
        用于ts_tick数据库，因为一个表有30GB，直接用原来的方法获取更新列表需要20分钟，太耗时了
        一次性函数，随着数据库清空，此函数将被停止使用
        """
        sql_1 = f"select code,date from ts_tick_status where (tick_status is null or tick_status = 0) and date between '{start_date.date()}' and '{end_date.date()}' order by date,code asc"
        df_main = pd.read_sql_query(sql_1, self.engine)
        for row in df_main.itertuples():
            code_jqdata = getattr(row, 'code')
            date = getattr(row, 'date')
            code = code_jqdata[0:6]
            #判断路径中是否存在相关数据
            t = os.path.exists(f".\\data\\tick\\{date}\\{code_jqdata}.csv")
            if t == True:
                #存在数据，直接进行删除操作
                try:
                    sql_d = f"delete from {table_name} where code = '{code}' and date(time) = '{date}';"                   
                    df = pd.read_sql_query( sql_d , self.engine)
                except:
                    print(f"{date} {code} 已删除")
            else:
                #不存在数据
                #读取并写入数据
                sql_2 = f"select time,price,`change`,volume,amount,type,`code` from {table_name} where code = '{code}' and date(time) = '{date}'"
                df = pd.read_sql_query(sql_2 , self.engine)
                count = df.shape[0]
                df['code'] = code_jqdata
                path = f".\\data\\tick\\{date.strftime('%Y-%m-%d')}\\"
                if not os.path.exists(path):
                    os.mkdir(path) 
                
                if count >0:
                    #有数据，进行存盘操作
                    df[['time','price','change','volume','amount','type','code']].to_csv(f"{path}{code_jqdata}.csv", encoding = 'utf_8_sig')
                #删除数据库数据并更新tick_status的对应日期和代码的数量
                try:
                    sql_u = f"update ts_tick_status set tick_status = {count} where code = '{code_jqdata}' and date = '{date}';"
                    df = pd.read_sql_query( sql_u , self.engine)                     
                except:
                    pass
                try:
                    sql_d = f"delete from {table_name} where code = '{code}' and date(time) = '{date}';"                    
                    df = pd.read_sql_query( sql_d , self.engine)                     
                except:
                    print(f"{date} {code} 已保存并删除，条目数{count}") 
if __name__=="__main__":
    tick = tick(rds_host = base.数据源.localhost , myauth = True)

    #新版的ts_tick导出程序 由于存在bug，start_date需要做动态调整，否则会重复输出
    tick.mysql_to_csv_V2(start_date = datetime.datetime(2021,1,14),end_date = datetime.datetime(2021,2,28))
    
    #12月
    #tick.mysql_to_csv_V2(start_date = datetime.datetime(2020,12,1),end_date = datetime.datetime(2020,12,31))
   
    #10-11月
    #tick.mysql_to_csv_V2(start_date = datetime.datetime(2020,10,30),end_date = datetime.datetime(2020,11,30))
    #数据校验模块，跑完所有的tick数据导出后可以重新拉一遍校验数据
    #tick.tick数量校验()
    
    #日常更新模块
    #tick.daily_update(start_date = datetime.datetime(2021,4,1),end_date = datetime.datetime.now())