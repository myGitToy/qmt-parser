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
            market：list 市场类别 默认主板/创业板/中小板/科创板/CDR/北交所
            day：datetime 日期 如果查询过去某一天的全部代码，day就是定位的坐标
            type：list 证券类型 stock/etf/lof
            --------->未来可能会加入市值筛选 基金份额筛选等内容
        【输出】
            dataframe:code|symbol|name|market|list_date
            #获取TS代码，股票代码，股票名称，所在地域，所属行业，市场类型等信息
        """
        df1 = self.pro.stock_basic(list_status='L', fields='ts_code,symbol,name,area,industry,market,list_status,list_date,delist_date,is_hs') 
        df2 = self.pro.stock_basic(list_status='D', fields='ts_code,symbol,name,area,industry,market,list_status,list_date,delist_date,is_hs') 
        df3 = self.pro.stock_basic(list_status='P', fields='ts_code,symbol,name,area,industry,market,list_status,list_date,delist_date,is_hs') 
        df = pd.concat([df1, df2, df3])
        df.rename(columns={"ts_code": "code", "delist_date": "date" } , errors="raise" , inplace = True)
        #df.drop(columns = ['trade_date','pre_close'] , inplace = True)
        #时间日期类的列进行类型变更
        df['list_date'] = pd.to_datetime(df['list_date'])
        df['date'] = pd.to_datetime(df['date'])
        df['date'].fillna(pd.to_datetime('2050-01-01') , inplace = True)
        df = df[df['date'] > self.end_date]
        return df

if __name__ == '__main__':
    a = pro_api()
    a.start_date = datetime(2020,1,1,8)
    a.end_date = datetime(2023,3,20,16)
    a.code = '159949.SZ'
    a.ktype = '1min'
    a.stock_basic()
    