import numpy as np
import pandas as pd
import tushare as ts
import sqlalchemy
import time
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

    def update_security_ETF(self ):
        """
        security日常更新(ETF和LOF资产)
        """
        #打印标题
        print("############正在准备更新security证券代码信息（ETF）###########")
        #读取ETF类资产
        df_security = self.pro.fund_basic(market = 'E')
        #print(df_security)
        #重命名为code
        df_security.rename(columns = {'ts_code':'code'} , inplace = True)
        df_security['list_date'] = pd.to_datetime(df_security['list_date'])
        df_security['delist_date'] = pd.to_datetime(df_security['delist_date'])       
        #退市日期同时设置为2099年12月31日
        df_security = df_security.fillna({'delist_date':datetime(2099,12,31)})
        #dataframe列名的数据类型进行映射
        dtypedict = {
            'code': NVARCHAR(length = 24),
            'name': NVARCHAR(length = 128),
            'management': NVARCHAR(length = 128),
            'custodian': NVARCHAR(length = 128),
            'fund_type': NVARCHAR(length = 24),
            'found_date': Date(),
            'due_date': Date(),
            'list_date': Date(),
            'issue_date': Date(),
            'delist_date': Date(),
            'issue_amount': Float(precision = 3, asdecimal = True),
            'm_fee': Float(precision = 3, asdecimal = True),
            'c_fee': Float(precision = 3, asdecimal = True),
            'duration_year': Float(precision = 3, asdecimal = True),
            'p_value': Float(precision = 3, asdecimal = True),
            'min_amount': Float(precision = 3, asdecimal = True),
            'exp_return': Float(precision = 3, asdecimal = True),
            'benchmark': NVARCHAR(length = 128),
            'status': NVARCHAR(length = 12),
            'invest_type': NVARCHAR(length = 64),
            'type': NVARCHAR(length = 64),
            'trustee': NVARCHAR(length = 128),
            'purc_startdate': Date(),
            'redm_startdate': Date(),
            'market': NVARCHAR(length = 8)
                    }
        #数据保存至数据库
        if df_security.empty == True:
            print("原始数据为空，无法导入数据库")
        else:
            df_security.to_sql(
                    name = 'tspro_fund_basic',
                    con = self.engine,
                    index = False,
                    if_exists = 'replace',
                    index_label='code' , #设置主键(设置未成功)
                    dtype=dtypedict) #映射列的数据类型

            with self.engine.connect() as con:
                #设置主键
                con.execute('ALTER TABLE `tspro_fund_basic` ADD PRIMARY KEY (`code`);')
                #设置索引（其实主键和索引一致的话，是可以不需要设置索引的）
                #con.execute('CREATE INDEX index `tspro_security` (`code`);')
            print(f"ETF数据已上传完成(security),新增数据{df_security.shape[0]}条")

    def update_security(self ,type = ['stock','index','fund','etf','lof','fja','fjb']):
        """
        security日常更新
        type jqdata证券类型，此处予以保留，实际无效果
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

    def get_all_code(self , market = ['主板','创业板','中小板','科创板','CDR','北交所'] , day = datetime.now() , type = ['stock','etf']):
        """
        获取本地数据库中的证券代码（按日期）
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
        获取指定证券代码的资产属性信息（简单版）
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

    def update_basic(self , sleep = 0.2):
        """
        接口：daily_basic，可以通过数据工具调试和查看数据。
        更新时间：交易日每日15点～17点之间
        描述：获取全部股票每日重要的基本面指标，可用于选股分析、报表展示等。
        数据自1991年开始
        """
        #获取更新列表（按交易日）
        trade_day = pd.DataFrame(columns = ['date'])
        trade_day = self.get_calendar(is_open = 1)
        #获取资金流向库中存在的日期列表
        query_daysql = f"select distinct date FROM tspro_basic FORCE INDEX (main) WHERE date BETWEEN '{self.start_date.date()}' and '{self.end_date.date()}'  ORDER BY date asc" 
        df_dbday = pd.read_sql_query(query_daysql , self.engine)
        if df_dbday.empty == True:
            #数据库不存在数据
            df_dbday = pd.DataFrame(columns = ['date'])
        else:
            #数据库存在数据
            df_dbday['date'] = pd.to_datetime(df_dbday['date']) #时间日期ns64化
            pass
        #数据拼接，最终需要更新的日期是trade_day中包含且df_dbday不包含的数据
        day_diff = pd.concat([trade_day , df_dbday , df_dbday]).drop_duplicates(subset = ['date'] , keep = False)
        print(day_diff)
        #打印标题
        print("############正在准备更新每日指标信息###########")
        """
        更新逻辑：
            1. 需要更新的日期
                1.1 取出区间内的交易日
                1.2 取出数据库中存在每日指标信息的日期
                1.3 两者取差集就是需要更新的日期
            2. 按照日期循环，获取每日的指标信息
            3. 数据写入数据库
        逻辑优点和不足：
            1. 一次性提取每日的指标信息，运行效率较高
            2. 智能化更新，跳过重复的日期
            3. 缺点：更新限制每次5000条，后续可能会超过限制值
        """
        for day in day_diff['date']:
            #获取数据库中存在的数据最后更新日期（加入强制使用索引的内容）
            df = self.pro.daily_basic(trade_date = day.strftime("%Y%m%d"))
            #重命名列（money_flow中的证券代码sec_code和数据库中的不一致）
            df.rename(columns = {'ts_code':'code','trade_date':'date'} , inplace = True)
            df['date'] = pd.to_datetime(df['date']) #时间日期ns64化
            #保存至数据库 
            if df.empty == True:
                print(f"{day.date()}数据为空，跳过上传")
            else:
                df.to_sql(
                        name = 'tspro_basic',
                        con = self.engine,
                        index = False,
                        if_exists = 'append')
                print(f"{day.date()} 数据已上传完成，更新条目数{df.shape[0]} (daily basic)")
                time.sleep(sleep)

    def get_basic(self , to_csv = True):
        """
        获取区间内最新的每日基本面数据
        """
        ###取出区间内的最后一个有效日期
        query_day = f"select distinct date FROM tspro_basic WHERE date BETWEEN '{self.start_date.date()}' and '{self.end_date.date()}'" 
        df_day = pd.read_sql_query(query_day , self.engine)
        if df_day.empty == True:
            #数据库不存在数据
            return pd.DataFrame()
        else:
            #数据库存在数据
            last_day = df_day.iloc[-1].at['date']
        ###通过区间内的最后一个有效日期来获取数据
        query_day = f"select * FROM tspro_basic WHERE date = '{last_day}'" 
        df_db = pd.read_sql_query(query_day , self.engine)
        if df_day.empty == True:
            #数据库不存在数据
            return pd.DataFrame()
        else:
            #数据库存在数据
            if to_csv ==  True:
                df_db.to_csv('.\\data\\海龟模型\\每日指标.csv', encoding = 'utf_8_sig')
            return df_db

if __name__=="__main__":
    #测试交易日历功能
    cal = security()
    cal.start_date = datetime(2023,1,1)
    cal.end_date = datetime(2023,8,9)
    cal.get_basic()
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

    