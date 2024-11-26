import numpy as np
import pandas as pd
import tushare as ts
import akshare as ak
from sqlalchemy import create_engine,exc,delete,text   #用来捕捉sqlalchemy的异常
from datetime import datetime
from apt.vendor.tspro.base import base as base
from apt.vendor.tspro.base import stock as stock
from sqlalchemy.types import NVARCHAR , Float, Integer , Date
from apt.vendor.tspro.security import security as tspro_sec

class security(base , stock):
    """
    专门处理security的类
    包含交易日历 交易列表
    """
    def update_calendar(self , exchange = 'SSE'):
        """
        更新交易日历（继承tspro同名方法）
        输入：
            exchange:交易所类型 默认更新上海交易所SSE
                    其他交易所包括：SSE上交所,SZSE深交所,CFFEX 中金所,SHFE 上期所,CZCE 郑商所,DCE 大商所,INE 上能源
        开始和结束日期由stock.XXX来定义
        更新逻辑：
            1. is_open在拉去api和数据导入阶段，不进行判断，导入全部的交易日和非交易日
            2. 数据导入进行差值导入，即比较新数据和原数据库，差异的部分进行导入
        """
        #继承tspro同名方法
        return tspro_sec.update_calendar(self)   

    def get_calendar(self , exchange = 'SSE' , is_open = 1 , all = False):
        """
        获取交易日历（继承tspro同名方法）
        输入：
            exchange：交易所代码 默认全部使用上交所信息 SSE上交所 SZSE深交所
            is_open：获取交易日的类型 默认剔除非交易日
                    0 非交易日
                    1 交易日
                    2 所有数据（用于交易日更新时进行两个df比较，非正常参数，平时不用）
        输出：
            date 交易日期
            is_open 交易日的类型
        """
        #继承tspro同名方法
        return tspro_sec.get_calendar(self)

    def update_security_ETF(self ):
        """
        security日常更新(ETF和LOF资产)（继承tspro同名方法）
        """
        #继承tspro同名方法
        return tspro_sec.update_security_ETF(self)

    def get_trade_date(self):
        """
        （未来函数预警）获取某一支股票在指定日期间的交易日列表（继承自tspro同名方法）
        """
        return tspro_sec.get_trade_date(self)

    def update_security(self ,type = ['stock','index','fund','etf','lof','fja','fjb']):
        """
        security日常更新（继承自tspro同名方法）
        type jqdata证券类型，此处予以保留，实际无效果
        """
        #继承tspro同名方法
        return tspro_sec.update_security(self,type)

    def get_all_code(self , market = ['主板','创业板','中小板','科创板','CDR','北交所'] , day = datetime.now() , type = ['stock','etf']):
        """
        获取本地数据库中的证券代码（按日期） 继承tspro同名方法
        【输入】
            market：list 市场类别 默认主板/创业板/中小板/科创板/CDR/北交所
            day：datetime 日期 如果查询过去某一天的全部代码，day就是定位的坐标
            type：list 证券类型 stock/etf/lof
            --------->未来可能会加入市值筛选 基金份额筛选等内容
        【输出】
            dataframe:code|symbol|name|market|list_date
        """
        #继承tspro同名方法
        return tspro_sec.get_all_code(self)

    def get_security(self , code = None):
        '''
        获取指定证券代码的资产属性信息（简单版）（继承tspro同名方法）
        返回
             dataframe , string
                df[0]:dataframe: code|market|name
                df[1]:string: stock|etf|nan           
        '''
        #继承tspro同名方法
        return tspro_sec.get_security(self)

               
if __name__=="__main__":
    #测试交易日历功能
    cal = security()
    cal.update_security_ETF()
    cal.start_date = datetime(1991,1,1)
    cal.end_date = datetime(2022,7,1)
    a =cal.get_security('601318.sh')
    print(a)
    print(cal.dict[cal.ktype])

    #测试ETF类资产更新
    #df = cal.update_security_ETF()
    #print(df)

    #测试stock和ETF类资产的读取 2022/7/10
    df = cal.get_all_code(type = ['etf','stock'] , day = cal.end_date)
    print(df)


    #df_up = cal.pro.query('limit_list_d' , trade_date = '20220616')
    #print(df_up)
    df_sec = cal.get_security(day = datetime(2001,1,1))
    print(df_sec)
    cal.ktype = '1m'
    print(cal.dict[cal.ktype])
    cal.update_security()

    a = base()
    sec = security()
    a.start_date = datetime(2022,1,1)
    a.end_date = datetime(2022,9,1)
    #df = a.pro.trade_cal(exchange='SZSE', list_status='D' ,   start_date='20180101', end_date='20181231')
    df = cal.pro.query('stock_basic', exchange='', list_status=['D','L'], fields='ts_code,symbol,name,area,industry,list_date')
    print(df)
    #测试交易日历读取功能
    df_read = sec.get_calendar()

    #测试基础数据 股票列表
    df_list = a.pro.stock_basic()
    print(df_list)

    