# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import tushare as ts
import akshare as ak
import sqlalchemy
from datetime import datetime,timedelta
from apt.qsp_universal.base import base
from sqlalchemy.types import NVARCHAR , Float, Integer , Date

class money_flow(base):
    """
    专门处理资金流向的类
    两种不同的资金流向：V1. 从tspro获取的传统资金流向（联网通过API方式）
                        V2. 从akshare 1分钟线价格 成交量转换过来的资金流向（从数据库获取）
    """
    def get_money_flow_V2(self , code = '600001.sh' , day = datetime(2023,1,1)):
        """
        从akshare 1分钟线价格 成交量转换过来的资金流向（单日资金流向）
        【输入】：
            code 证券代码
            day 交易日期
        【输出】
        """
        #交易日检查（暂未开通）
        #self.code = code 
        #self.end_date = day
        #self.ktype = '1m'
        #单日资金流向
        a = self.__get_1min_flow(code = self.code , day = self.end_date)
        #df = self.get_k_data()
        return 

    def __get_1min_flow(self , code = '600001.sh' , day = datetime(2023,1,1)):
        """
        从akshare 1分钟线价格 成交量转换过来的资金流向（单日资金流向）
        【输入】：
            code 证券代码
            day 交易日期
        【输出】
        """
        #交易日检查（暂未开通）
        #self.code = code 
        #self.end_date = day
        #self.ktype = '1m'

        #a = base()
        #a.code = code
        #a.start_date = day.date() + timedelta(hours = 8)
        #a.end_date = day.date() + timedelta(hours = 16)
        #a.ktype = self.ktype
        #a.vendor = self.vendor
        df = self.get_k_data().sort_values(by = ['date'] )
        print(df)
        #删除9:30和15:00的数据
        df = df.query('date.dt.time != datetime.strptime("09:30","%H:%M").time()')
        df = df.query('date.dt.time != datetime.strptime("15:00","%H:%M").time()')
        df['close_diff'] = df['close'] - df['close'].shift(1)
        #np.where单独使用，符合条件的返回array组，再使用iloc进行定位和修订
        df['money_flow'] = np.nan
        #df.iloc[np.where(df['close_diff'] > 0)]['money_flow'] = 1
        df['money_flow'] = np.where(df['close_diff'] > 0 , df['money'] , df['money_flow'] )
        df['money_flow'] = np.where(df['close_diff'] < 0 , -df['money'] , df['money_flow'] )
        df['money_flow'] = np.where(df['close_diff'] == 0 , 0 , df['money_flow'] )
        df['cumsum'] = df['money_flow'].cumsum()
        print(df)
        # 对时间进行一下处理
        df['date'] = pd.to_datetime(df['date'],format = "%m-%d")
        df.set_index('date',inplace=True)
        #print(df[['date','close','close_diff','money','money_flow','cumsum']])
        #统一各股资金流向的坐标轴，统一按照1个million来计算，也就是对应的1e7
        df['cumsum'] = df['cumsum'] / 1000000
        num = df.iloc[-1].at['cumsum']
        return num            
if __name__=="__main__":
    #测试资金流向
    a = money_flow()
    a.code = '600389.sh'
    a.start_date = datetime(2023,7,18,8)
    a.end_date = datetime(2023,7,18,16)
    a.ktype = '1m'
    a.vendor = base.vendor.akshare
    dd = a.get_money_flow_V2(code = '600389.sh' , day = datetime(2023,7,18))
    print(dd)

    