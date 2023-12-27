# -*- coding: utf-8 -*-
from datetime import datetime,date,timedelta
from apt.vendor.tspro.base import base as base
from apt.vendor.tspro.base import stock as stock
from apt.vendor.tspro.data import data as data
import tushare as ts
import pandas as pd
import numpy as np
import pandas as pd

class pro_api(data):
    """
    tushare pro数据接口层，调用方法请参看task 449
    https://huiqiao.visualstudio.com/MyFunds/_sprints/taskboard/MyFunds%20Team/MyFunds/2023Q1?workitem=449
    """
    def __init__(self):
        #初始化 接入token
        self.pro = ts.pro_api("55297f16c0119146589e059db315ba28a9412e89ec9f91e538e655b2")
    def stock_basic(self , end_date = datetime(2022,1,1)):
        """
        获取本地数据库中的证券代码（按日期）
        与vendor.tspro.security.get_all_code()的区别
        此处：调用pro_api方法，仅可在线访问
        get_all_code：从本地数据库获取数据
        【输入】
            通过self.end_date传值过来的日期，用于定位某一个具体的日期，用于和上市退市日期进行比较
        【输出】
            dataframe:code 证券代码|symbol 股票代码6位数字|name 证券名称|area 地域|industry 所属行业|
            market 市场类型|list_status 上市状态 L上市 D退市 P暂停上市|list_date 上市日期|date 退市日期|
            is_hs 是否沪深港通标的，N否 H沪股通 S深股通
        """
        df1 = self.pro.stock_basic(list_status='L', fields='ts_code,symbol,name,area,industry,market,list_status,list_date,delist_date,is_hs') 
        df2 = self.pro.stock_basic(list_status='D', fields='ts_code,symbol,name,area,industry,market,list_status,list_date,delist_date,is_hs') 
        df3 = self.pro.stock_basic(list_status='P', fields='ts_code,symbol,name,area,industry,market,list_status,list_date,delist_date,is_hs') 
        df = pd.concat([df1, df2, df3])
        df.rename(columns={"ts_code": "code" } , errors="raise" , inplace = True)
        #df.drop(columns = ['trade_date','pre_close'] , inplace = True)
        #时间日期类的列进行类型变更
        df['list_date'] = pd.to_datetime(df['list_date'])
        df['delist_date'] = pd.to_datetime(df['delist_date'])
        df['delist_date'].fillna(pd.to_datetime('2050-01-01') , inplace = True)
        #df = df[df['delist_date'] > self.end_date & df['list_date'] < self.end_date ] #测试未通过
        #df.query(f'list_date <= {self.end_date} or delist_date >= {self.end_date}')    #测试未通过
        df = df.loc[(df['list_date'] <= self.end_date) & (df['delist_date'] >= self.end_date)]
        return df

    def suspend_k(self ,  suspend_type = 'S') -> pd.DataFrame:
        """
        获取某一天停牌的股票
        【输入】
            start_date:开始日期（系统自带）
            end_date:结束日期 （系统自带）
            suspend_type:停牌类型：S-停牌 R-复牌
        【输出】
            dataframe:code 证券代码|date 交易日期|suspend_timing 停牌时间段|suspend_type 停牌类型：S-停牌 R-复牌
        【格式】
            125  831039.BJ 2023-03-03           None            S
            126  001337.SZ 2023-03-03    09:30-10:00            S
            127  603061.SH 2023-03-03    09:30-10:00            S
            128  830974.BJ 2023-03-03           None            S

        拆分全天停牌和临时停牌
            全天停牌：df.query('suspend_timing != suspend_timing')
            临时停牌：df.query('suspend_timing == suspend_timing')
        """
        df = self.pro.suspend_d(start_date = self.start_date.strftime('%Y%m%d') , end_date = self.end_date.strftime('%Y%m%d') , suspend_type = suspend_type)
        if df.shape[0] >= 4999:
            raise Exception(f'停牌数据超过5000条，请检查起止时间段')
        df.rename(columns={"ts_code": "code" ,"trade_date" : "date"} , errors="raise" , inplace = True)
        df["date"] = pd.to_datetime(df["date"])
        return df
    

if __name__ == '__main__':
    a = pro_api()
    a.start_date = datetime(2023,3,1,8)
    a.end_date = datetime(2023,3,20,16)
    a.code = '159949.SZ'
    a.ktype = '1min'
    #df = a.stock_basic()
    df = a.suspend_k()
    pd.set_option('display.max_rows', None)  # Set display option to show all rows
    df = df.dropna(subset=['suspend_timing'])  # Filter out rows with 'None' values in 'suspend_timing' column
