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
        更新交易日历（仅从tspro迁移 未修改代码）
        输入：
            exchange:交易所类型 默认更新上海交易所SSE
                    其他交易所包括：SSE上交所,SZSE深交所,CFFEX 中金所,SHFE 上期所,CZCE 郑商所,DCE 大商所,INE 上能源
        开始和结束日期由stock.XXX来定义
        更新逻辑：
            1. is_open在拉去api和数据导入阶段，不进行判断，导入全部的交易日和非交易日
            2. 数据导入进行差值导入，即比较新数据和原数据库，差异的部分进行导入
        """
        #打印标题
        print("############正在准备更新security证券日历信息###########")
        #1. 读取api中的交易日数据
        df_cal = self.pro.trade_cal(exchange = exchange, start_date = self.start_date.strftime("%Y%m%d"), end_date = self.end_date.strftime("%Y%m%d"))
        #数据类型转换(否则差值计算会出错)       
        df_cal.rename(columns={"cal_date": "date"} , errors="raise" , inplace = True)
        df_cal['date'] = pd.to_datetime(df_cal['date'])
        df_cal['pretrade_date'] = pd.to_datetime(df_cal['pretrade_date'])
        #df_cal['date'].astype('datetime64[D]')
        #2. 读取本地数据库中已存在的数据
        df_db = self.get_calendar(exchange = exchange ,is_open = 2 )
        #数据类型转换(否则差值计算会出错)
        df_db['date'] = pd.to_datetime(df_db['date'])
        #3. 将两者进行比较
        #Feature Warning Fix
        df_cal = df_cal.dropna(how='all', axis=1)
        df_db = df_db.dropna(how='all', axis=1)        
        df_diff = pd.concat([df_cal , df_db , df_db] ).drop_duplicates(subset=['date'],keep = False)
        #4. 数据保存至数据库
        if df_diff.empty == True:
            print("日期差值为空，无需导入数据库")
        else:
            df_diff.to_sql(
                    name = 'tspro_calendar',
                    con = self.engine,
                    index = False,
                    if_exists = 'append')
            print(f"数据已上传完成(交易日历)，新增数据{df_diff.shape[0]}条")

    def get_calendar(self , exchange = 'SSE' , is_open = 1 , all = False):
        """
        获取交易日历（仅从tspro迁移 未修改代码）
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
        if is_open == 2:
            #读取全部数据
            query = f"select exchange,date,is_open,pretrade_date FROM tspro_calendar WHERE exchange = '{exchange}' and date BETWEEN '{self.start_date.date()}' and '{self.end_date.date()}'" 
        else:
            #按正常逻辑对is_open进行处理
            query = f"select date,is_open FROM tspro_calendar WHERE exchange = '{exchange}' and is_open = {is_open} and date BETWEEN '{self.start_date.date()}' and '{self.end_date.date()}'" 
        df_db = pd.read_sql_query(query , self.engine)
        #排序和数据归一化
        df_db['date'] = pd.to_datetime(df_db['date'])
        df_db.sort_values(by = ['date'] , ascending = True , inplace = True)
        if df_db.empty == True:
            #数据库不存在数据
            return pd.DataFrame()
        else:
            #数据库存在数据
            return df_db

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
        security日常更新（继承自tspro）
        type jqdata证券类型，此处予以保留，实际无效果
        """
        #继承tspro同名方法
        return tspro_sec.update_security(self,type)

    def get_all_code(self , market = ['主板','创业板','中小板','科创板','CDR','北交所'] , day = datetime.now() , type = ['stock','etf']):
        """
        获取本地数据库中的证券代码（按日期）（仅从tspro迁移 未修改代码）
        【输入】
            market：list 市场类别 默认主板/创业板/中小板/科创板/CDR/北交所
            day：datetime 日期 如果查询过去某一天的全部代码，day就是定位的坐标
            type：list 证券类型 stock/etf/lof
            --------->未来可能会加入市值筛选 基金份额筛选等内容
        【输出】
            dataframe:code|symbol|name|market|list_date
        """
        #脱机查询
        market_type = ','.join(["'%s'" % item for item in market ])
        type_string = ','.join(["'%s'" % item for item in type ])
        df_main = pd.DataFrame()
        for tp in type:
            #按照类型循环读取
            if tp == 'stock':
                #读取股票类代码
                df = pd.read_sql_query(f"select * from tspro_security where '{day.date()}' between list_date and delist_date and market in ({market_type})" , self.engine)
                df_main = pd.concat([df_main , df[['code','symbol','name','market','list_date']]] , sort = False )
            elif tp == 'etf':
                #读取ETF类代码
                df = pd.read_sql_query(f"select * from tspro_fund_basic where '{day.date()}' between list_date and delist_date and market = 'E'" , self.engine)
                df_main = pd.concat([df_main , df[['code','name','market','list_date']]] , sort = False )
            elif tp == 'lof':
                #读取ETF类代码
                raise ValueError(f'暂不支持LOF代码')
            else:
                #其他类型
                raise ValueError(f'暂不支持该类型代码')
            
        if df_main.empty == True:
            #数据库不存在数据
            return pd.DataFrame()
        else:
            #数据库存在数据，返回
            return df_main

    def get_security(self , code = None):
        '''
        获取指定证券代码的资产属性信息（简单版）（仅从tspro迁移 未修改代码）
        返回
             dataframe , string
                df[0]:dataframe: code|market|name
                df[1]:string: stock|etf|nan           
        '''
        string = f"""select code,market,name from tspro_security where code = '{code}'
                    union ALL
                    select code,market,name from tspro_fund_basic where code =  '{code}'"""
        df = pd.read_sql_query(string , self.engine)
        if df.shape[0] == 0:
            #无数据
            return pd.DataFrame() , np.nan
        if df.iloc[0].at['market'] == 'E':
            #返回ETF
            return df[['code','market','name']] , 'etf'
        else:
            #返回stock
            return df[['code','market','name']] ,'stock'
               
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

    