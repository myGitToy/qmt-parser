import numpy as np
import pandas as pd
import tushare as ts
import sqlalchemy
from datetime import datetime
from apt.vendor.tspro.base import base as base
from apt.vendor.tspro.base import stock as stock
from sqlalchemy.types import NVARCHAR , Float, Integer , Date

class security(base , stock):
    """
    专门处理security的类
    包含交易日历 交易列表
    """
    def update_calendar(self , exchange = 'SSE'):
        """
        更新交易日历
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
        获取交易日历
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

    def update_security(self ,type = ['stock','index','fund','etf','lof','fja','fjb']):
        """
        security日常更新
        type 证券类型，支持多选 默认为全部（目前不包含期货）
        """
        pro = ts.pro_api()
        #打印标题
        print("############正在准备更新security证券代码信息###########")
        df_security = pd.DataFrame()
        #设置需要更新的证券列表状态，默认只读取上市的，在回溯过往会带来一些未来函数的问题
        list_status = ['D','L','P']
        for list in list_status:
            df = pro.query('stock_basic', list_status = list , fields='ts_code,symbol,name,area,industry,fullname,enname,cnspell,market,exchange,curr_type,list_status,list_date,delist_date,is_hs')
            #数据拼接
            df_security = pd.concat([df_security , df] , sort = False )
        #重命名为code
        df_security.rename(columns = {'ts_code':'code'} , inplace = True)
        df_security['list_date'] = pd.to_datetime(df_security['list_date'])
        df_security['delist_date'] = pd.to_datetime(df_security['delist_date'])       
        #退市日期同时设置为2099年12月31日
        df_security = df_security.fillna({'delist_date':datetime(2099,12,31)})
        #dataframe列名的数据类型进行映射
        dtypedict = {
            'code': NVARCHAR(length = 24),
            'symbol': NVARCHAR(length = 128),
            'name': NVARCHAR(length = 128),
            'area': NVARCHAR(length = 128),
            'industry': NVARCHAR(length = 128),
            'fullname': NVARCHAR(length = 128),
            'enname': NVARCHAR(length = 128),
            'cnspell': NVARCHAR(length = 24),
            'market': NVARCHAR(length = 12),
            'exchange': NVARCHAR(length = 12),
            'curr_type': NVARCHAR(length = 12),
            'list_status': NVARCHAR(length = 8),
            'list_date': Date(),
            'delist_date': Date(),
            'is_hs': NVARCHAR(length = 8)
                    }
        #数据保存至数据库
        if df_security.empty == True:
            print("原始数据为空，无法导入数据库")
        else:
            df_security.to_sql(
                    name = 'tspro_security',
                    con = self.engine,
                    index = False,
                    if_exists = 'replace',
                    index_label='code' , #设置主键(设置未成功)
                    dtype=dtypedict) #映射列的数据类型

            with self.engine.connect() as con:
                #设置主键
                con.execute('ALTER TABLE `tspro_security` ADD PRIMARY KEY (`code`);')
                #设置索引（其实主键和索引一致的话，是可以不需要设置索引的）
                #con.execute('CREATE INDEX index `tspro_security` (`code`);')
            print(f"数据已上传完成(security),新增数据{df_security.shape[0]}条")

    def get_security(self , market = "'主板','创业板','中小板','科创板','CDR','北交所'" , day = datetime.now()):
        """
        获取本地数据库中的证券代码（按日期）
        【输入】
            market：市场类别 默认主板/创业板/中小板/科创板/CDR/北交所
        【输出】
            dataframe:code|symbol|name|market|list_date
        """
        #脱机查询
        df = pd.read_sql_query(f"select * from tspro_security where  '{day.date()}' between list_date and delist_date and market in ({market})" , self.engine)
        if df.empty == True:
            #数据库不存在数据
            return pd.DataFrame()
        else:
            #数据库存在数据，返回
            return df[['code','symbol','name','market','list_date']]


               
if __name__=="__main__":
    #测试交易日历功能
    cal = security()
    cal.start_date = datetime(1991,1,1)
    cal.end_date = datetime(1991,9,1)
    print(cal.dict[cal.ktype])
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

    