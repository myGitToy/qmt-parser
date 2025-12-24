import numpy as np
import pandas as pd
import tushare as ts
import sqlalchemy
import akshare as ak
import time
from sqlalchemy import create_engine,exc,delete,text   #用来捕捉sqlalchemy的异常
from datetime import datetime,timedelta
from apt.vendor.tspro.security import security  as security
from apt.vendor.akshare.base import base as base
from apt.vendor.akshare.base import stock as stock
from apt.vendor.tspro.security import security
from pandas.io import sql as con
from sqlalchemy import text
from apt.vendor.tspro.pro_api import pro_api as pro_api
from apt.vendor.tspro.security import security as security
from apt.vendor.tspro.data import data as tspro_data
#加入tqdm支持
from tqdm import tqdm
# 新增：Eastmoney cookies 确保与修复版接口
# cookies模块将直接在需要时导入
from apt.vendor.akshare.fixes import fixed_stock_zh_a_hist_min_em
from apt.vendor.akshare.fixes import fixed_fund_etf_hist_min_em
#from apt.vendor.tspro.security import get_calendar

#加入redis和json支持
from apt.os.redis.redisHandler import RedisClientWrapper as redisClient
import json
import traceback

class data(base,stock):
    """
    数据接口 基类
    所有需要从tusharePro获取数据的都需要从此处引用
    引用规范：from apt.vendor.tspro.data import data as data
    例：量化选股 qsp_jqdata就是从这里作为基类引用的
    
    def __init__(self, rds_host=base.数据源.localhost, myauth=True , code = None , start = datetime(2021,1,1), end = datetime.now() , ktype = "1d" , fq = base.复权.动态复权 ):
        self.__init__()
        super().__init__()
        
        #super().__init__(rds_host = rds_host, myauth = myauth)
        #super().__init__(code = code , start_date = start , end_date = end , ktype = ktype , fq = fq)
    """
    #def __init__(self):
        #super(data , self).__init__()

    def update_day(self , flag_verify_db = True):
        """
        ***akshare日线更新模块，调用tushare数据源和方法，此处只做引用，不做任何更新***
        tusharePro数据日常更新的主入口（按天更新）
        输入：
        flag_verify_db T/F值 是否进行当日数据校验 默认是False 不进行校验，进行差集更新
            True 进行校验，如有 则跳过更新（速度最快，但可能会漏，尤其是先更新ETF后更新stock，则stock会漏更新）
            Flase 不进行数据库数量校验 即忽略当日库中原有的ETF或者stock数据，进入差集更新（速度较慢，但能保证完整性）
        本模块只支持日线格式更新（日线数据按日进行全部数据的获取，因此与分时线的逻辑有所不同）
        更新逻辑：
            1. 获取需要更新的时间周期中的交易日
            2. 循环读取证券代码列表进行更新
                2.1 读取数据库中单个代码在两个日期间的数据
                2.2 没有数据则直接写入操作
                2.3 存在数据，则去重后写入
        """
        print("############正在准备更新stock日线数据###########")
        #日线类型校验
        if self.ktype != '1d':
            raise ValueError(f'分时线数据请使用update_min函数进行更新')
        #更新时段校验 如果更新的是日线数据且校验为更新时段，则不予以更新
        #check = self.get_today_is_trade()
        check = None
        if check == self.交易时段校验.交易时段:
            raise ValueError(f'update_V1规则不允许在交易时段进行更新')
        #获取交易日期
        trade_days = self.pro.trade_cal(exchange = 'SSE', start_date = self.start_date.strftime('%Y%m%d'), end_date=self.end_date.strftime('%Y%m%d'))
        #剔除非交易日
        trade_days.query('is_open == 1' , inplace = True)
        trade_days['cal_date'] = pd.to_datetime(trade_days['cal_date'])
        for day in trade_days['cal_date']:
            #print(f"##############正在更新%s数据##############" % day.strftime("%Y-%m-%d"))
            #检查数据库是否存在数据（目前跳过验证，数据查询耗时较长）
            query = f"select MIN(date) , count(date) as num from tspro_{self.ktype} where date(date) = '{day.date()}'"
            df_old = pd.read_sql_query(query , self.engine)
            count = df_old.loc[0 , 'num']
            if count > 0 and flag_verify_db == True:
                #同时满足两种情况：数据库存在数据且忽略ETF数据，则跳过更新
                #此处存在数据，不进入更新序列，直接跳过
                print(f"{day.strftime('%Y-%m-%d')}存在数据且忽略当日数据，跳过更新")
            else:
                #不存在数据 或者进入差集更新模式
                if  self.ktype == '1d':
                    df = self.pro.daily(trade_date= day.strftime('%Y%m%d'))
                    #根据wiki描述的数据库一致性的要求，进行列名的变更 https://huiqiao.visualstudio.com/MyFunds/_wiki/wikis/MyFunds.wiki/19/tusharePro%E6%95%B0%E6%8D%AE%E8%AF%8D%E5%85%B8
                    #df.rename(columns={'ts_code': 'code', 'trade_date': 'date' , 'vol': 'volume' , 'amount': 'money'} , errors="raise")
                    #df.rename(columns={"ts_code": "code", "trade_date": "date" } , errors="raise")
                    #TO DO: 如果数据集为空，会报错，需要增加一个判断
                    df.rename(columns={"ts_code": "code", "trade_date": "date" ,"vol" : "volume" , "amount" : "money"} , errors="raise" , inplace = True)
                    #删除列
                    df.drop(columns = ['pre_close','change','pct_chg'] , inplace = True)                 
                    #时间日期类的列进行类型变更
                    df['date'] = pd.to_datetime(df['date'])
                    #volume成交量列从手转换成股 统一乘100
                    #df['volume'].astype(np.float)
                    df['volume'] = df['volume'] * 100
                    #amount成交金额列从千元转换成元，统一乘1000
                    #df['money'].astype(np.float)
                    df['money'] = df['money'] * 1000
                    #日线数据特殊处理，因为数据库中的格式是date，不是datetime
                    #df = df[(df.date == day)]
                    #差集处理，此处更新了SQL语句，解决查询时间过慢的问题
                    query = f"select code , date from tspro_{self.ktype} where date = '{day.date()}'"
                    df_db = pd.read_sql_query(query , self.engine)
                    df_db['date'] = pd.to_datetime(df_db['date'])
                    #Feature Warning Fix
                    df = df.dropna(how='all', axis=1)
                    df_db = df_db.dropna(how='all', axis=1)
                    df = pd.concat([df , df_db , df_db ]).drop_duplicates(subset = ['code','date'] , keep = False)
                else:
                    #分时数据正常处理
                    #############这里留一个问题，是否可以用df.date.date() == day的形式进行筛选
                    #进行当天数据的筛选，因为比如取5m数据，当天有48根，但可能上午停牌，因此48根数据就包含了昨天下午的，此时写入数据库会造成唯一索引约束错误
                    df = get_bars(security = code , count = update_num , unit = ktype , fields = ['date', 'open', 'close', 'high', 'low', 'volume', 'money','factor'] , include_now = False , end_dt = end_day , df = True)
                    if df.empty == True:
                        #增加一个判断和筛选，因为正常情况下不会出错，但是如果代码未上市，此时df不会取到前面几天，而是直接返回空值
                        #PS 日线部分竟然不影响，挺神奇的
                        pass
                    else:
                        df['code']= code
                        df = df[(df.date.dt.date == day)]
                        #df = df[(df.date >= datetime.datetime(day.year,day.month,day.day,1)) & (df.date <= datetime.datetime(day.year,day.month,day.day,16))]
                #保存至数据库
                if df.empty == True:
                    print("%s 当日数据为空或者差集为空，跳过上传" % (day.strftime('%Y%m%d')))
                else:
                    df.to_sql(
                            name = f'tspro_{self.ktype}',
                            con = self.engine,
                            index = False,
                            if_exists = 'append')
                    print(f"{day.strftime('%Y%m%d')}数据已上传完成({self.ktype})")

    def update_day_ETF(self):
        """
        ***akshare日线更新模块，调用tushare数据源和方法，此处只做引用，不做任何更新***
        tusharePro基金数据日常更新的主入口（按天更新）
        本模块只支持日线格式更新（日线数据按日进行全部数据的获取，因此与分时线的逻辑有所不同）
        更新逻辑：
            1. 获取需要更新的时间周期中的交易日
            2. 数据取差集后插入数据库
        """
        print("############正在准备更新ETF日线数据###########")
        #日线类型校验
        if self.ktype != '1d':
            raise ValueError(f'分时线数据请使用update_min函数进行更新')
        #更新时段校验 如果更新的是日线数据且校验为更新时段，则不予以更新
        #check = self.get_today_is_trade()
        check = None
        if check == self.交易时段校验.交易时段:
            raise ValueError(f'update_V1规则不允许在交易时段进行更新')
        #获取交易日期
        trade_days = self.pro.trade_cal(exchange = 'SSE', start_date = self.start_date.strftime('%Y%m%d'), end_date=self.end_date.strftime('%Y%m%d'))
        #剔除非交易日
        trade_days.query('is_open == 1' , inplace = True)
        trade_days['cal_date'] = pd.to_datetime(trade_days['cal_date'])
        for day in trade_days['cal_date']:
            #print(f"##############正在更新%s数据##############" % day.strftime("%Y-%m-%d"))
            #检查数据库是否存在数据（目前跳过验证，数据查询耗时较长）
            query = f"select code,date from tspro_{self.ktype} where date(date) = '{day.date()}'"
            df_db = pd.read_sql_query(query , self.engine)
            df = self.pro.fund_daily(trade_date = day.strftime('%Y%m%d'))
            df.rename(columns={"ts_code": "code", "trade_date": "date" ,"vol" : "volume" , "amount" : "money"} , errors="raise" , inplace = True)
            #删除列
            df.drop(columns = ['pre_close','change','pct_chg'] , inplace = True)                 
            #时间日期类的列进行类型变更
            df['date'] = pd.to_datetime(df['date'])
            df_db['date'] = pd.to_datetime(df_db['date'])
            #volume成交量列从手转换成股 统一乘100
            #df['volume'].astype(np.float)
            df['volume'] = df['volume'] * 100
            #amount成交金额列从千元转换成元，统一乘1000
            #df['money'].astype(np.float)
            df['money'] = df['money'] * 1000
            #日线数据特殊处理，因为数据库中的格式是date，不是datetime
            #两者取差集(df-df_db)主要目的是为了导入ETF复权因子，因此主集设定为df
            #Feature Warning Fix
            df = df.dropna(how='all', axis=1)
            df_db = df_db.dropna(how='all', axis=1)
            df = pd.concat([df , df_db , df_db]).drop_duplicates(subset=['code','date'] , keep = False)
            #print(df)
            #保存至数据库
            if df.empty == True:
                print("%s 当日数据为空或者差集为空，跳过上传" % (day.strftime('%Y%m%d')))
            else:
                df.to_sql(
                        name = f'tspro_{self.ktype}',
                        con = self.engine,
                        index = False,
                        if_exists = 'append')
                print(f"{day.strftime('%Y%m%d')}数据已上传完成(ETF日线)")    

    def update_sequence_add(self , code_list = None , myclass = 'stock' , type = '60m'  , priority = 0 , auto_select = True):
        '''
        task346更改了分时线数据更新的逻辑，拆分成add和launch两部分
        add模块主要进行数据更新任务的导入
        输入：
            code_list 需要更新的证券代码列表，有列表（优先更新）和无列表（正常更新）进入的是两个不同的流程
            myclass 一级目录 默认stock  目前可接受参数stock|etf
            type 二级目录 默认60m；目前可接受参数：60m/1m
            priority 优先更新标识 默认为0
            auto_select 是否自动选择1，默认为True
        '''
        if code_list != None:
            ######流程1：优先更新逻辑，混合代码，需要拉取证券列表的类型等数据
            ######       此时myclass类型无效；type有效；priority为1
            sec = security()
            df_main = pd.DataFrame()
            for code in code_list:
                #按每条数据，分别获取信息并写入数据库
                myclass = sec.get_security(code = code)[1]
                if myclass != np.nan:
                    record = {'code':code,'start_date':self.start_date,'end_date':self.end_date,'class':myclass,'type':type,'priority':1}                             
                    df_main = pd.concat([df_main,pd.DataFrame(record,index = [0])])
                                         
                    #pd.DataFrame(record,ignore_index = True)]) #pandas 2.0版本后，不再支持append
                    #df_main.append(record , ignore_index = True)
                    #df = pd.DataFrame()
                    #df['code'] = code
                    #df['start_date'] = self.start_date
                    #df['end_date'] = self.end_date
                    #df['class'] = myclass
                    #df['type'] = type
                    #df['priority'] = 1
                #df_main = pd.concat([df_main,df])
            #写入数据库
            df_main.to_sql(
                    name = f'akshare_update_sequence',
                    con = self.engine,
                    index = False,
                    if_exists = 'append')
            print(f"优先更新列表上传已完成，新增{df_main.shape[0]}条更新序列！")

        else:
            ######流程2：正常更新逻辑，ETF或者Stock
            ######       此时code_list无效；myclass类型有效；type有效；priority为0
            #class数据校验
            if myclass not in ['stock','etf']:
                raise ValueError(f'无效的数据类型(一级目录)')
            #type数据校验
            if type not in ['1d','60m','1m','5m']:
                raise ValueError(f'无效的数据类型(二级目录)')
            #分时线类型校验
            if self.ktype == '1d' or type == '1d':
                raise ValueError(f'日线数据请使用update_day函数进行更新')
            #点断续传数据库条目数校验
            sql_count = 'select count(id) as count from akshare_update_sequence'
            df_db = pd.read_sql_query(sql_count , self.engine)
            if df_db.iloc[0].at['count'] == 0:
                #数据库不存在数据
                result = '1' 
            else:
                #数据库存在数据
                if auto_select == True:
                    result = '1'
                else: #数据库存在数据，且不自动选择
                    try:
                        result = input('''数据库存在数据，请选择更新方式 \n
                        1. 保留原有更新序列，添加新的序列 \n
                        2. 删除原有更新序列，添加新的序列 \n
                        3. 删除原有更新序列 \n
                        4. 退出（不做任何处理）\n''')
                    except EOFError:
                        #在VS2022环境中出现以下错误：
                            #分析“EOFError       (note: full exception trace is shown but execution is paused at: <module>)”错误
                        #备注：VS Code无此问题
                            result = '1'
            if result == '1':               #添加新数据
                #1. 获取区间最后一天所对应的全部证券列表
                sec = security()
                if myclass == 'stock':
                    code_list = sec.get_all_code(day = self.end_date , type = ['stock'])
                elif myclass == 'etf':
                    code_list = sec.get_all_code(day = self.end_date , type = ['etf'])
                code_list['start_date'] = self.start_date
                code_list['end_date'] = self.end_date
                code_list['class'] = myclass
                code_list['type'] = type
                code_list = code_list[['code','start_date','end_date','class','type']]
                code_list['priority'] = priority
                code_list.to_sql(
                        name = f'akshare_update_sequence',
                        con = self.engine,
                        index = False,
                        if_exists = 'append')
                print(f"上传已完成，新增{code_list.shape[0]}条更新序列！")

            elif result == '2':             #删除后添加
                sql_count = text('delete from akshare_update_sequence')
                try:
                    with self.engine.begin() as connection:
                        connection.execute(sql_count)
                except exc.ResourceClosedError:
                    print(f"删除更新序列失败！")
                #以下代码与选项1保持一致
                #1. 获取区间最后一天所对应的全部证券列表
                sec = security()
                if myclass == 'stock':
                    code_list = sec.get_all_code(day = self.end_date , type = ['stock'])
                elif myclass == 'etf':
                    code_list = sec.get_all_code(day = self.end_date , type = ['etf'])
                code_list['start_date'] = self.start_date
                code_list['end_date'] = self.end_date #add模块中日期不需要+1
                code_list['class'] = myclass
                code_list['type'] = type
                code_list = code_list[['code','start_date','end_date','class','type']]
                code_list['priority'] = priority
                code_list.to_sql(
                        name = f'akshare_update_sequence',
                        con = self.engine,
                        index = False,
                        if_exists = 'append')
                print(f"上传已完成，新增{code_list.shape[0]}条更新序列！")

            elif result == '3':             #直接删除
                sql_count = text('delete from akshare_update_sequence')
                try:
                    with self.engine.begin() as connection:
                        connection.execute(sql_count)
                except exc.ResourceClosedError:
                    print(f"删除更新序列失败！")

            elif result == '4':          #不做任何更改，直接跳出
                return 
            else:
                raise ValueError(f'无效的输入')

    def update_sequence_launch(self , priority = 0 , sleep = 0.05):
        '''
        task346更改了分时线数据更新的逻辑，拆分成add和launch两部分
        launch模块主要进行数据更新任务，支持点断续传
        priority 是否优先更新 默认为0
        sleep 每条数据更新的间隔时间 默认0.05 需要流出一定的间隔，否则会被服务器强制下线
        '''
        # 先确保 Eastmoney cookies（会自动处理缓存和过期逻辑）
        try:
            from apt.vendor.akshare.cookies import get_em_cookie
            cookies = get_em_cookie(force_refresh=False, save_to_env_file=False)
            if cookies:
                print("已获取Eastmoney cookies，将用于数据请求")
            else:
                print("未能获取Eastmoney cookies，继续无cookies模式进行数据更新")
        except Exception as e:
            print(f"Eastmoney cookies 获取失败: {e}，继续无 cookies 模式进行数据更新")

        #处理是否优先更新
        if priority == 1:
            #优先更新
            sql = "select * from akshare_update_sequence where priority = 1" 
        else:
            #没有优先更新列表 全部加载
            sql = "select * from akshare_update_sequence" 
        df_sequence = pd.read_sql_query(sql , self.engine)
        code_list = df_sequence['code']
        if df_sequence.shape[0] > 0 :
            #有数据，进行更新
            #设定最大更新行数
            max_row = 8000
            for index, row in tqdm(df_sequence.iterrows(), total=len(df_sequence), desc="正在更新证券数据"):
                id = row['id']
                code = row['code']
                if len(code) == 6:
                    symbol = code
                else:
                    symbol = code[0:6]
                #print(symbol)
                #start_date = datetime.strftime(row['start_date'] , '%Y-%m-%d')
                #end_date  = datetime.strftime(row['end_date'] , '%Y-%m-%d')
                start_date = row['start_date']
                end_date  = row['end_date']
                myclass = row['class']
                type = row['type']
                #tspro pro_bar数据获取模块（这里对最后日期做了day+1的处理）
                net_connection = True
                if myclass == 'stock':
                    #df_tspro = ts.pro_bar(api = self.api , ts_code = code, freq = self.dict[type] , adj = None , start_date = start_date.strftime('%Y%m%d') , end_date = (end_date + timedelta(days = 1)).strftime('%Y%m%d') , adjfactor = True , factors = ['tor', 'vr'] , asset = 'E')
                    #print(self.dict[type])
                    try:
                        df_ak = pd.DataFrame()
                        df_ak =  fixed_stock_zh_a_hist_min_em(symbol = symbol , start_date = start_date.strftime('%Y%m%d %H:%M:%S'), end_date = end_date.strftime('%Y%m%d %H:%M:%S'), period = self.dict[type], adjust = '')
                    except:
                        print("网络连接失败！")
                        df_ak = pd.DataFrame()  # 修复：网络失败时清空df_ak，防止写入错误数据
                        net_connection = False
                    #print(df_ak)
                elif myclass == 'etf':
                    #df_ak = ts.pro_bar(api = self.api , ts_code = code, freq = self.dict[type] , adj = None , start_date = start_date.strftime('%Y%m%d') , end_date = (end_date + timedelta(days = 1)).strftime('%Y%m%d') , adjfactor = True , asset = 'FD')

                    
                    try:
                        df_ak =  fixed_fund_etf_hist_min_em(symbol = symbol , start_date = start_date.strftime('%Y%m%d %H:%M:%S'), end_date = end_date.strftime('%Y%m%d %H:%M:%S'), period = self.dict[type], adjust = '')                
                    except Exception as e:
                        df_ak = pd.DataFrame()
                        print(f"{code} akshare ETF/LOF数据更新错误: {e}")
                        traceback.print_exc()
                #print(df_ak)
                #最大数据量校验
                if df_ak.shape[0] >= max_row:
                    raise ValueError(f'接收到的数据达到最大允许值，可能存在数据丢失，中止更新！')
                #数据适配1：对于akshare的分钟线，额外丢弃一部分内容
                """
                场内数据（证券）分时（1分钟线）
                    akshare1.12版本： 日期   开盘   收盘   最高   最低   成交量  成交额  最新价
                    akshare1.14版本： 时间   开盘   收盘   最高   最低   成交量  成交额  均价
                场内数据（ETF）分时（1分钟线）
                    akshare1.12版本： 日期   开盘   收盘   最高   最低   成交量  成交额  振幅  最新价
                    akshare1.14版本： 时间   开盘   收盘   最高   最低   成交量  成交额  均价
                场内数据（证券）分时（60/30/5分钟线）
                    akshare1.12版本： 时间   开盘   收盘   最高   最低  涨跌幅  涨跌额   成交量  成交额  振幅  换手率
                    akshare1.14版本： 时间   开盘   收盘   最高   最低  涨跌幅  涨跌额   成交量  成交额  振幅  换手率
                    升级后无差异
                akshare1.12版本：
                    1分钟线需要去除 ：振幅  最新价
                    60分钟线需要去除：涨跌幅  涨跌额 振幅  换手率
                akshare1.14版本：
                    1分钟线需要去除 ：均价
                    60分钟线需要去除： 同1.12版本 
                akshare1.16版本：
                    2025/2/18发现ak1分钟线出现更新错误，升级akshare版本后问题修复
                """
                if type =='1m' and net_connection == True:
                    #print(df_ak)
                    if df_ak.shape[0] != 0:
                        if myclass == 'stock':  
                            #print(df_ak)
                            # 容错：只删除存在的列
                            cols_to_drop = [col for col in ['均价', '最新价'] if col in df_ak.columns]
                            if cols_to_drop:
                                df_ak.drop(columns=cols_to_drop, inplace=True)
                        elif myclass == 'etf':
                            # 容错：只删除存在的列
                            cols_to_drop = [col for col in ['均价', '最新价'] if col in df_ak.columns]
                            if cols_to_drop:
                                df_ak.drop(columns=cols_to_drop, inplace=True)
                        else:
                            pass
                    else:
                        pass
                    #df_ak.rename(columns={"日期": "时间"} , errors="raise" , inplace = True)
                elif type in ['60m','30m','5m'] and net_connection == True:
                    if df_ak.shape[0] != 0:
                        # 容错：只删除存在的列
                        cols_to_drop = [col for col in ['涨跌幅','涨跌额','振幅','换手率'] if col in df_ak.columns]
                        if cols_to_drop:
                            df_ak.drop(columns=cols_to_drop, inplace=True)
                else:
                    print('无法识别的类型')
                #数据适配2：增加证券代码列
                df_ak['code'] = code
                #df_ak['symbol'] = symbol   #暂不将symbol列写入数据库
                if df_ak.shape[0] != 0 and net_connection == True:
                    #数据适配3：列的名字做变更
                    df_ak.rename(columns={"时间": "date", "开盘": "open" ,"收盘" : "close" , "最高" : "high" , "最低" : "low" , "成交量" : "volume" , "成交额" : "money"} , errors="raise" , inplace = True)
                    #数据适配4：成交量的单位为手 ，需要乘以100
                    df_ak['volume'] = df_ak['volume'] * 100
                    #print(df_ak)
                    #时间日期类的列进行类型变更
                    df_ak['date'] = pd.to_datetime(df_ak['date'])
                    #日期排序(目前判定下为非必要，预留代码，减小数据更新的压力)
                    #df_tspro.sort_values(columns = ['date'], inplace = True , ascending = False)
                else:
                    pass
                #分时线数据不需要进行成交量和成交额修正
                #4. 获取数据库对应日期的数据
                query_db = f"select code,date,open,close,high,low,volume,money from akshare_{type} where date(date) between '{start_date.date()}' and '{end_date.date()}' and code = '{code}'"
                df_db = pd.read_sql_query(query_db , self.engine)
                df_db['date'] = pd.to_datetime(df_db['date'])
                #测试两个df格式
                #print(df_ak)
                #print(df_db)
                #5. 两个DataFrame进行差值处理
                #Feature Warning Fix
                df_ak = df_ak.dropna(how='all', axis=1)
                df_db = df_db.dropna(how='all', axis=1)
                df_diff = pd.concat([df_ak , df_db , df_db] ).drop_duplicates(subset=['date'] , keep = False)
                #6. 差值数据写入数据库
                if df_diff.empty == True:
                    print(f"{code}差值数据为空，跳过更新")
                else:
                    df_diff.to_sql(
                            name = f'akshare_{type}',
                            con = self.engine,
                            index = False,
                            if_exists = 'append')
                    print(f"{code}数据已上传完成({type}，新增数据{df_diff.shape[0]})")
                    #数据导入增加XX毫秒的延迟（akshare专有，速度太快会被限制）
                    time.sleep(sleep)
                #7. 将此条目从更新序列中删除
                """
                这部分代码注释，原因是用pd.read_sql_query方法，在现有版本中无法对数据条目做删除操作
                详见https://huiqiao.visualstudio.com/MyFunds/_workitems/edit/499/
                sql_delete = text(f'delete from tspro_update_sequence where id = {id}')
                try:    #删除需捕捉异常，否则会报错
                    pd.read_sql_query(sql_delete , self.engine)
                except exc.ResourceClosedError:
                    pass
                """
                if net_connection == True:
                    #只有网络链接成功时，才进行删除操作
                    sql_delete = text(f"delete from akshare_update_sequence where id = {id}")
                    try:
                        with self.engine.begin() as connection:
                            connection.execute(sql_delete)
                    except exc.ResourceClosedError:
                        print(f"删除{code}更新序列失败！")
                        pass  
                else:
                    #保留更新序列
                    print(f"{code}网络连接失败，保留更新序列")
        else:
            #无数据，跳过
            print("更新序列无数据，跳过更新")

    def update_min(self):
        """
        ***akshare更新模块，调用tushare数据源和方法，此处只做引用，不做任何更新***
        tusharePro数据日常更新的主入口（按天按每代码进行更新）
        进行历史数据更新时需要注意，由于系统设定，返回的最大row为8000行，本模块代码内部做了相应的提示
        task349重要提示：
            目前分时线已做点断续传的处理，整体函数入口拆分成add和launch两部分，请注意
        重要事项：
            更新2022/6/14-2022/6/16数据时，实际只会更新6/14 15两天，6/16并不会更新
            原因在于6/16当天的数据不符合datetime(2022,6,16)的条件
            解决方案：请输入带时间的格式 datetime(2022,6,16,23)
        
        start_date 开始时间，由基类参数控制
        end_date 结束时间，由基类参数控制
        ktype K线周期 1d 5m 60m等
        
        更新逻辑：
            1. 获取需要更新的时间周期中的交易日
            2. 循环读取证券代码列表进行更新
                2.1 读取数据库中单个代码在两个日期间的数据
                2.2 没有数据则直接写入操作
                2.3 存在数据，则去重后写入
        """
        raise ValueError
        #分时线类型校验
        if self.ktype == '1d':
            raise ValueError(f'日线数据请使用update_day函数进行更新')
        #设定最大更新行数
        max_row = 8000
        #更新时段校验 交易时段不允许更新
        #check = self.get_today_is_trade()
        check = None        #这里先关闭交易时段校验
        if check == self.交易时段校验.交易时段:
            raise ValueError(f'update_V1规则不允许在交易时段进行更新')
        #1. 获取区间最后一天所对应的全部证券列表
        sec = security()
        code_list = sec.get_all_code(day = self.end_date)
        #2. 获取交易日期（代码暂时移除，目前按照区间更新）
        trade_days = self.pro.trade_cal(exchange = 'SSE', start_date = self.start_date.strftime('%Y-%m-%d %H:%M:%s'), end_date = self.end_date.strftime('%Y-%m-%d %H:%M:%s'))
        #剔除非交易日
        trade_days.query('is_open == 1' , inplace = True)
        trade_days['cal_date'] = pd.to_datetime(trade_days['cal_date'])
        #3. 获取tspro相应的数据
        for code in code_list['code']:
            #目前量比 vor 复权因子均无效 
            #tspro pro_bar数据获取模块（这里对最后日期做了day+1的处理）
            df_tspro = ts.pro_bar(api = self.api , ts_code = code, freq = self.dict[self.ktype] , adj = None , start_date = self.start_date.strftime('%Y-%m-%d %H:%M:%s') , end_date = (self.end_date + timedelta(days = 1)).strftime('%Y-%m-%d %H:%M:%s') , adjfactor = True , factors = ['tor', 'vr'] , asset = 'E')
            #最大数据量校验
            if df_tspro.shape[0] >= max_row:
                raise ValueError(f'接收到的数据达到最大允许值，可能存在数据丢失，中止更新！')
            #print(df_tspro)
            df_tspro.rename(columns={"ts_code": "code", "trade_time": "date" ,"vol" : "volume" , "amount" : "money"} , errors="raise" , inplace = True)
            df_tspro.drop(columns = ['trade_date','pre_close'] , inplace = True)
            #时间日期类的列进行类型变更
            df_tspro['date'] = pd.to_datetime(df_tspro['date'])
            #日期排序(目前判定下为非必要，预留代码，减小数据更新的压力)
            #df_tspro.sort_values(columns = ['date'], inplace = True , ascending = False)
            #分时线数据不需要进行成交量和成交额修正
            #4. 获取数据库对应日期的数据
            query_db = f"select code,date,open,close,high,low,volume,money from tspro_{self.ktype} where date(date) between '{self.start_date.date()}' and '{self.end_date.date()}' and code = '{code}'"
            #TO DO：上述查询语句是否可以做优化？
            
            df_db = pd.read_sql_query(query_db , self.engine)
            df_db['date'] = pd.to_datetime(df_db['date'])
            #print(df_tspro)
            #5. 两个DataFrame进行差值处理
            #Feature Warning Fix
            df_tspro = df_tspro.dropna(how='all', axis=1)
            df_db = df_db.dropna(how='all', axis=1)
            df_diff = pd.concat([df_tspro , df_db , df_db] ).drop_duplicates(subset=['date'] , keep = False)
            #6. 差值数据写入数据库
            if df_diff.empty == True:
                print(f"{code}差值数据为空，跳过更新")
            else:
                df_diff.to_sql(
                        name = f'tspro_{self.ktype}',
                        con = self.engine,
                        index = False,
                        if_exists = 'append')
                print(f"{code}数据已上传完成({self.ktype}，新增数据{df_diff.shape[0]})")

    def update_ak_resample(self):
        """
        本模块用于将akshare1m数据重采样后，比对5m和60m的数据，差集再写回数据库
        """        
        # 基础数据准备：获取全部证券代码
        print("############正在准备更新akshare分时线数据(5m 60m 重采样)###########")
        df_all_code = security.get_all_code(self)   
        for code in df_all_code['code']:
            self.code = code
            self.resample_1m_to_5m(flash_to_database=True)
            self.resample_1m_to_60m(flash_to_database=True)
        print("############akshare分时线数据重采样完成###########")


    def code_ts_to_ak(self):
        """
        将tushare代码类型转换成akshare类型
        """
        #代码类型校验
        if self.code[6:7] == ".":
            #tushare数据类型，返回ak类型
            return self.code[7:9] + self.code[0:6]
        else:
            return self.code
        
    def code_ak_to_ts(self , code_ak):
        """
        将akshare代码类型转换成tushare类型
        """
        #代码类型校验
        if len(code_ak) == 6:
            #这是akshare数据类型，返回tushare代码code 
            query = f"select code from tspro_security where symbol = '{code_ak}'"
            df_db = pd.read_sql_query(query , self.engine)
            #如果dataframe不为空且数据仅有一行，返回code
            if df_db.shape[0] == 1:
                return df_db.loc[0 , 'code']
            else:
                raise ValueError(f'无效的证券代码')
        elif len(self.code) == 9:
            #9位数字，则默认为tushare代码，直接返回
            return self.code
        else:
            raise ValueError(f'无效的证券代码')

    def get_ak_factor(self):
        """
        从akshare处获取复权因子
        返回：
            0：升序排列日期|复权因子Dataframe
            1：最后一个复权因子

        """
        #代码类型转换
        ak_code = self.code_ts_to_ak()
        hfq_factor_df = ak.stock_zh_a_daily(symbol=f"{ak_code}", adjust="hfq-factor")
        hfq_factor_df.rename(columns={"hfq_factor": "factor", "date": "factor_date" } , errors="raise" , inplace = True)
        #时间日期类的列进行类型变更
        hfq_factor_df['factor_date'] = pd.to_datetime(hfq_factor_df['factor_date'])
        #复权因子进行类型变更
        hfq_factor_df['factor'] = hfq_factor_df['factor'].astype('float')
        #顺序翻转 正序排列
        #数据类型转换
        hfq_factor_df.sort_values(by="factor_date",axis=0,ascending=True, inplace=True, na_position="last")
        #print(hfq_factor_df)
        return hfq_factor_df , hfq_factor_df.iloc[-1].at['factor']

    def get_ts_ak(self):
        #获取带授权的
        pass

    def update_factor(self , flag_verify_db = False):
        """
        ***akshare更新模块，调用tushare数据源和方法，此处只做引用，不做任何更新***
        tusharePro复权因子日常更新的主入口（按天更新）
        flag_verify_db T/F值 是否进行当日数据校验 默认是False 不进行校验，进行差集更新
            True 进行校验，如有 则跳过更新（速度最快，但可能会漏，尤其是先更新ETF后更新stock，则stock会漏更新）
            Flase 不进行数据库数量校验 即忽略当日库中原有的ETF或者stock数据，进入差集更新（速度较慢，但能保证完整性）
        更新逻辑：
            1. 获取需要更新的时间周期中的交易日
            2. 循环读取证券代码列表进行更新
                2.1 读取数据库中单个代码在两个日期间的数据
                2.2 没有数据则直接写入操作
                2.3 存在数据，则去重后写入
        """
        print("############正在准备更新stock复权因子###########")
        #获取交易日期
        trade_days = self.pro.trade_cal(exchange = 'SSE', start_date = self.start_date.strftime('%Y%m%d'), end_date=self.end_date.strftime('%Y%m%d'))
        #剔除非交易日
        trade_days.query('is_open == 1' , inplace = True)
        trade_days['cal_date'] = pd.to_datetime(trade_days['cal_date'])
        for day in trade_days['cal_date']:
            #print(f"##############正在更新%s数据##############" % day.strftime("%Y-%m-%d"))
            #检查数据库是否存在数据（目前跳过验证，数据查询耗时较长）
            query = f"select MIN(date) , count(date) as num from tspro_factor where date = '{day.date()}'"
            df_old = pd.read_sql_query(query , self.engine)
            count = df_old.loc[0 , 'num']
            if count > 0 and flag_verify_db == True:
                #此处存在数据，不进入更新序列，直接跳过
                print(f"{day.strftime('%Y-%m-%d')}存在数据且忽略当日数据，跳过更新")
            else:
                #1. 不存在数据 无关忽略与否，进行更新
                #2. 存在数据，且不忽略数据库当日原有数据
                #不存在数据，或者进入差集更新模式
                df = self.pro.query('adj_factor',  trade_date = day.strftime('%Y%m%d'))
                #print(df)
                #df = self.pro.daily(trade_date= day.strftime('%Y%m%d'))
                #根据wiki描述的数据库一致性的要求，进行列名的变更 https://huiqiao.visualstudio.com/MyFunds/_wiki/wikis/MyFunds.wiki/19/tusharePro%E6%95%B0%E6%8D%AE%E8%AF%8D%E5%85%B8
                #df.rename(columns={'ts_code': 'code', 'trade_date': 'date' , 'vol': 'volume' , 'amount': 'money'} , errors="raise")
                #df.rename(columns={"ts_code": "code", "trade_date": "date" } , errors="raise")
                df.rename(columns={"ts_code": "code", "trade_date": "date" ,"adj_factor" : "factor" } , errors="raise" , inplace = True)           
                #时间日期类的列进行类型变更
                df['date'] = pd.to_datetime(df['date'])
                #差集处理
                query = f"select code , date from tspro_factor where date(date) = '{day.date()}'"
                df_db = pd.read_sql_query(query , self.engine)
                df_db['date'] = pd.to_datetime(df_db['date'])
                #Feature Warning Fix
                df = df.dropna(how='all', axis=1)
                df_db = df_db.dropna(how='all', axis=1)
                df = pd.concat([df , df_db , df_db ]).drop_duplicates(subset = ['code','date'] , keep = False)
                #保存至数据库
                if df.empty == True:
                    print("%s 当日数据为空或者差集为空，跳过上传" % (day.strftime('%Y%m%d')))
                else:
                    df.to_sql(
                            name = f'tspro_factor',
                            con = self.engine,
                            index = False,
                            if_exists = 'append')
                    print(f"{day.strftime('%Y%m%d')}复权因子已上传完成")

    def update_factor_ETF(self , flag_ignore_database = True):
        """
        ***akshare更新模块，调用tushare数据源和方法，此处只做引用，不做任何更新***
        tusharePro基金数据复权因子日常更新的主入口（按天更新）
        更新逻辑：
            1. 获取需要更新的时间周期中的交易日
            2. 循环读取证券代码列表进行更新
                2.1 读取数据库中单个代码在两个日期间的数据
                2.2 没有数据则直接写入操作
                2.3 存在数据，则去重后写入
        """
        print("############正在准备更新ETF复权因子###########")
        #获取交易日期
        trade_days = self.pro.trade_cal(exchange = 'SSE', start_date = self.start_date.strftime('%Y%m%d'), end_date=self.end_date.strftime('%Y%m%d'))
        #剔除非交易日
        trade_days.query('is_open == 1' , inplace = True)
        trade_days['cal_date'] = pd.to_datetime(trade_days['cal_date'])
        for day in trade_days['cal_date']:
            #print(f"##############正在更新%s复权因子数据（ETF）##############" % day.strftime("%Y-%m-%d"))
            #检查数据库是否存在数据（目前跳过验证，数据查询耗时较长）
            query = f"select code,date,factor from tspro_factor where date(date) = '{day.date()}'"
            df_db = pd.read_sql_query(query , self.engine)
            df = self.pro.fund_adj(trade_date = day.strftime('%Y%m%d'))
            #ts数据处理
            df.rename(columns={"ts_code": "code", "trade_date": "date" ,"adj_factor" : "factor" } , errors="raise" , inplace = True)           
            #时间日期类的列进行类型变更
            df['date'] = pd.to_datetime(df['date'])
            df_db['date'] = pd.to_datetime(df_db['date'])
            #两者取差集(df-df_db)主要目的是为了导入ETF复权因子，因此主集设定为df
            #Feature Warning Fix
            df = df.dropna(how='all', axis=1)
            df_db = df_db.dropna(how='all', axis=1)            
            df = pd.concat([df , df_db , df_db] ).drop_duplicates(subset=['code','date'] , keep = False)
            #保存至数据库
            if df.empty == True:
                print("%s 当日数据为空或者差集为空，跳过上传" % (day.strftime('%Y%m%d')))
            else:
                df.to_sql(
                        name = f'tspro_factor',
                        con = self.engine,
                        index = False,
                        if_exists = 'append')
                print(f"{day.strftime('%Y%m%d')}复权因子已上传完成(ETF)")

    def get_k_data(self , count = None , col = ['code','date','open','close','high','low','volume','money','factor'] , flag_forward = False , flag_resample = False):
        
        """
        tspro数据加载模块（目前不支持输出N日后的X条数据，详见https://huiqiao.visualstudio.com/MyFunds/_workitems/edit/296）
        start_time：开始时间 最好带上小时参数  比如(2020,12,31,8)
        end_time：结束时间 最好带上小时参数  比如(2020,12,31,16)
        count : 获取K线条目的个数 默认是全部输出  
        flag_forward：用于获取N日之后X条数据，类似于后复权数据 默认为False
            在这种模式下，start_date为基准日期，先后输出count条数据
            其余模式end_date 均为基准日期
            详见https://huiqiao.visualstudio.com/MyFunds/_workitems/edit/296
        flag_resample：T/F 用于标识是否进行重采样 60分钟线目前无法重采样，因为默认按照整点小时划分
            无论设置如何，resample只对tushare数据有效，akshare60分钟线每日正常有4条数据，无需重采样
            目前仅对60分钟线有效
            True：进行重采样
            False：不进行重采样，舍弃9:30单根数据（akshare的数据格式无9:30数据）
        接受前复权 后复权 不复权 动态复权四种复权模式
        成交量、成交额目前未进行复权处理
        返回的数据格式：
            code,date,open,high,low,close,volume,money,factor
            升序排列（backtrader要求的数据格式）
        """
        #akshare数据无需重采样
        self.resample = False
        if self.start_date  > self.end_date:
            raise ValueError(f'开始日期必须早于结束日期')
        if self.ktype not in ['1d','1m','5m','30m','60m']:
            raise ValueError(f'不合规的K线类型: {self.ktype}')
        if self.code == None :
            raise ValueError(f'证券代码不能为空')
        #获取tspro数据
        #这里说明如下：这步的tspro数据目的是两个数据供应商之间的数据做拼接
        #query语句需要根据日线还是分时线做不同的处理
        if self.ktype == '1d':
            #日线数据由于是日期格式，需要加入.date()进行格式化
            query_tspro = f"select code,date,open,high,low,close,volume,money from tspro_{self.ktype} where code = '{self.code}' and date BETWEEN '{self.start_date.date()}' and '{self.end_date.date()}' order by date asc"   
        else:
            query_tspro = f"select code,date,open,high,low,close,volume,money from tspro_{self.ktype} where code = '{self.code}' and date BETWEEN '{self.start_date}' and '{self.end_date}' order by date asc"      
        try:
            df_tspro = pd.read_sql_query(query_tspro , self.engine)
            #print(df_tspro)
        except:
            #数据获取异常，说明数据库不存在或者有其他问题，直接返回空，表明tspro的数据没有
            df_tspro = pd.DataFrame()
        #获取akshare数据（目前ak只有分时数据，无日线数据，因此返回tspro的原始数据）
        if self.ktype =='1d':
            #日线返回空
            df_ak = df_tspro
        else:
            #分时线查询ak
            query_ak = f"select code,date,open,high,low,close,volume,money from akshare_{self.ktype} where code = '{self.code}' and date BETWEEN '{self.start_date}' and '{self.end_date}' order by date asc"         
            df_ak = pd.read_sql_query(query_ak , self.engine)
        #取数据交集
        #df_db = pd.merge(df_tspro,df_ak,on=['code','date'],how='inner')
        #Feature Warning Fix
        df_tspro = df_tspro.dropna(how='all', axis=1)
        df_ak = df_ak.dropna(how='all', axis=1)
        df_db = pd.concat([df_tspro , df_ak ] ).drop_duplicates(subset=['date'] , keep = 'first')
        #print(df_db)
        #处理需要返回的个数
        if count == None:
            #返回全部
            count = len(df_db)
        if df_db.empty == True:
            #无数据
            return pd.DataFrame()
        else:
            #有数据，进行复权处理
            #定义日线 分时数据新列factor_date用于拼接复权因子
            if self.ktype == '1d':
                df_db['factor_date'] = pd.to_datetime(df_db['date'], format="%Y-%m-%d")
            else:
                df_db['factor_date'] = pd.to_datetime(df_db['date'].dt.date)
            #获取复权因子
            tspro_factor = self.get_tspro_factor()
            tspro_factor['factor_date'] = tspro_factor['date']
            #复权因子与K线数据进行拼接（复权因子和K线数据只有要一处空值，最后拼接的数据就会有所缺失）
            df_db = pd.merge(df_db, tspro_factor[['factor_date','factor']] , on = ['factor_date'] , how = 'left')
            #复权因子修正完毕，填充后进入复权处理（tspro每天均有复权因子，此处无需填充）
            #df_db.ffill(axis=0, inplace=True, limit=None, downcast=None)
            #进行60分钟线修正（akshare无需修正）

            if self.fq.value == 0:  #不复权
                if flag_forward == False:
                    #正常模式
                    return df_db.iloc[-count:][col]
                else:
                    #非正常模式，以start_date为基准输出向后的count条记录
                    return df_db.iloc[:count][col]
            elif self.fq.value ==1 :  #前复权
                #前复权价格 = 当日价格 / 最后一个交易日（非end_date）的复权因子 * 当日复权因子
                factor = self.__get_last_factor()
                df_db['open'] = df_db['open'] / factor * df_db['factor']
                df_db['high'] = df_db['high'] / factor * df_db['factor']
                df_db['low'] = df_db['low'] / factor * df_db['factor']
                df_db['close'] = df_db['close'] / factor * df_db['factor']
                if flag_forward == False:
                    #正常模式
                    return df_db.iloc[-count:][col]
                else:
                    #非正常模式，以start_date为基准输出向后的count条记录
                    return df_db.iloc[:count][col]
            elif self.fq.value == 2:    #后复权
                #后复权价格 = 当日价格 / 第一个交易日（start_date）的复权因子 * 当日复权因子    
                #获取第一一个复权因子的数值
                factor = df_db.iloc[0].at['factor']
                df_db['open'] = df_db['open'] / factor * df_db['factor']
                df_db['high'] = df_db['high'] / factor * df_db['factor']
                df_db['low'] = df_db['low'] / factor * df_db['factor']
                df_db['close'] = df_db['close'] / factor * df_db['factor']
                if flag_forward == False:
                    #正常模式
                    return df_db.iloc[-count:][col]
                else:
                    #非正常模式，以start_date为基准输出向后的count条记录
                    return df_db.iloc[:count][col]
            elif self.fq.value == 3:    #动态复权
                #动态复权价格 = 当日价格 / 区间最后一天的复权因子 * 当日复权因子
                #获取最后一个复权因子的数值
                factor = df_db.iloc[-1].at['factor']
                df_db['open'] = df_db['open'] / factor * df_db['factor']
                df_db['high'] = df_db['high'] / factor * df_db['factor']
                df_db['low'] = df_db['low'] / factor * df_db['factor']
                df_db['close'] = df_db['close'] / factor * df_db['factor']
                if flag_forward == False:
                    #正常模式
                    return df_db.iloc[-count:][col]
                else:
                    #非正常模式，以start_date为基准输出向后的count条记录
                    return df_db.iloc[:count][col]
            else:
                raise ValueError(f'不支持的复权模式，请检查！')
                return df_db

    def __get_last_factor(self , day = datetime(2020,12,1)):
        """
        获取指定股票的最后复权因子（内部函数）
        """
        query = f"select date,factor from tspro_factor where code = '{self.code}' and date >= '{day.date()}' order by date desc limit 1"       
        df_db = pd.read_sql_query(query , self.engine)
        return df_db.iloc[0].at['factor']

    def get_tspro_factor(self):
        """
        获取tspro的复权因子
        无需输入start_date和end_date
        """
        sql = f"select date,code,factor from tspro_factor where code = '{self.code}' and date(date) between '{self.start_date.date()}' and '{self.end_date.date()}'"
        df_db = pd.read_sql_query(sql , self.engine)
        df_db['date'] = pd.to_datetime(df_db['date'] , format="%Y-%m-%d")
        return df_db

    def __get_k_data_ak(self , code = None ,  count = None , col = ['code','date','open','close','high','low','volume','money','factor'] , flag_forward = False):      
        """
        这里是获取AK的复权因子，暂时不使用 保留备用
        tspro数据加载模块（目前不支持输出N日后的X条数据，详见https://huiqiao.visualstudio.com/MyFunds/_workitems/edit/296）
        --------->复权数据采用akshare <---------
        start_time：开始时间 最好带上小时参数  比如(2020,12,31,8)
        end_time：结束时间 最好带上小时参数  比如(2020,12,31,16)
        count : 获取K线条目的个数 默认是全部输出  
        flag_forward：用于获取N日之后X条数据，类似于后复权数据 默认为False
            在这种模式下，start_date为基准日期，先后输出count条数据
            其余模式end_date 均为基准日期
            详见https://huiqiao.visualstudio.com/MyFunds/_workitems/edit/296
        接受前复权 后复权 不复权 动态复权四种复权模式
        成交量、成交额目前未进行复权处理
        返回的数据按照升序排列（backtrader要求的数据格式）
        """
        raise ValueError('已移除该项功能')
        if self.start_date  > self.end_date:
            raise ValueError(f'开始日期必须早于结束日期')
        if self.ktype not in ['1d','1m','5m','30m','60m']:
            raise ValueError(f'不合规的K线类型: {ktype}')
        if self.code == None :
            raise ValueError(f'证券代码不能为空')
        query = f"select * from tspro_{self.ktype} where code = '{self.code}' and date BETWEEN '{self.start_date}' and '{self.end_date}' order by date asc"         
        df_db = pd.read_sql_query(query , self.engine)
        #处理需要返回的个数
        if count == None:
            #返回全部
            count = len(df_db)
        if df_db.empty == True:
            #无数据
            #print("无数据")
            return pd.DataFrame()
        else:
            #有数据，进行复权处理（由于ts不带授权信息，首先先要将ak除权因子和ts数据进行拼接）
            #定义日线 分时数据新列factor_date用于拼接复权因子
            df_db['factor_date'] = pd.to_datetime(df_db['date'], format="%Y-%m-%d")
            #获取复权因子
            ak_factor = self.get_ak_factor()
            #复权因子与K线数据进行拼接
            df_db = df_db.merge(ak_factor[0] , how = 'left' , on = 'factor_date')
            #复权因子修正
            #这里因为numpy对于空值的判断和常理不太符合，因此采用另一种方法判断空置
            #正常理解应该使用==np.nan
            if np.isnan(df_db.loc[0,'factor']):
                #第一个复权因子为空，进行填充
                #起始日期前的第一个复权因子
                ak_factor_start = ak_factor[0].query('factor_date <= @self.start_date').iloc[-1].at['factor']
                #print(f'日期前的最后一个复权因子为{ak_factor_start}')
                #复权因子赋值于df_db第一个对应的单元格
                df_db.loc[0,'factor'] = ak_factor_start
            #复权因子修正完毕，进行填充
            df_db.ffill(axis=0, inplace=True, limit=None, downcast=None)
            if self.fq.value == 0:  #不复权
                if flag_forward == False:
                    #正常模式
                    return df_db.iloc[-count:][col]
                else:
                    #非正常模式，以start_date为基准输出向后的count条记录
                    return df_db.iloc[:count][col]
            elif self.fq.value ==1 :  #前复权
                #前复权价格 = 当日价格 / 最后一个交易日（非end_date）的复权因子 * 当日复权因子
                factor = ak_factor[1]
                print(type(factor))
                df_db['open'] = df_db['open'] / factor * df_db['factor']
                df_db['high'] = df_db['high'] / factor * df_db['factor']
                df_db['low'] = df_db['low'] / factor * df_db['factor']
                df_db['close'] = df_db['close'] / factor * df_db['factor']
                if flag_forward == False:
                    #正常模式
                    return df_db.iloc[-count:][col]
                else:
                    #非正常模式，以start_date为基准输出向后的count条记录
                    return df_db.iloc[:count][col]
            elif self.fq.value == 2:    #后复权
                #后复权价格 = 当日价格 / 第一个交易日（start_date）的复权因子 * 当日复权因子    
                #获取第一一个复权因子的数值
                factor = df_db.iloc[0].at['factor']
                df_db['open'] = df_db['open'] / factor * df_db['factor']
                df_db['high'] = df_db['high'] / factor * df_db['factor']
                df_db['low'] = df_db['low'] / factor * df_db['factor']
                df_db['close'] = df_db['close'] / factor * df_db['factor']
                if flag_forward == False:
                    #正常模式
                    return df_db.iloc[-count:][col]
                else:
                    #非正常模式，以start_date为基准输出向后的count条记录
                    return df_db.iloc[:count][col]
            elif self.fq.value == 3:    #动态复权
                #动态复权价格 = 当日价格 / 区间最后一天的复权因子 * 当日复权因子
                #获取最后一个复权因子的数值
                factor = df_db.iloc[-1].at['factor']
                df_db['open'] = df_db['open'] / factor * df_db['factor']
                df_db['high'] = df_db['high'] / factor * df_db['factor']
                df_db['low'] = df_db['low'] / factor * df_db['factor']
                df_db['close'] = df_db['close'] / factor * df_db['factor']
                if flag_forward == False:
                    #正常模式
                    return df_db.iloc[-count:][col]
                else:
                    #非正常模式，以start_date为基准输出向后的count条记录
                    return df_db.iloc[:count][col]
            else:
                raise ValueError(f'不支持的复权模式，请检查！')
                return df_db

    def fix_1min_error_v3(self, day = datetime(2023,12,1)):
            """
            第三版的更新逻辑（正在开发中）
            自2025/4起东财做了更新限制，目前比较难获取5m数据，因此第三版针对这一情况做修正
            本模块使用日线数据对1分钟线进行数据修正，目前存在以下几个问题：
            1. 当日停盘个股在1分钟线上是有数据的（成交量为0），如果隔日截取，则停盘日取不到1分钟数据；
            2. 如果对历史的1分钟数据进行截取，则开盘价open均为0（1分钟线数据仅保留5天）
            3. 当日临时停盘，未知

            【输入】
                start_date
                end_date

                
            【处理逻辑】
                重采样：1m线重新采样60m的规则为采样成4根K线
                9:30:00-10:30:00 采样定义为10:30:00
                10:31:00-11:30:00 采样定义为11:30:00
                13:00:00-14:00:00 采样定义为14:00:00
                14:01:00-15:00:00 采样定义为15:00:00


                重采样：1m线重新采样5m的规则为采样成48根K线
                9:30:00-09:35:00 采样定义为09:35:00
                09:36:00-09:40:00 采样定义为09:40:00
                ...
                11:26:00-11:30:00 采样定义为11:30:00
                11:31:00-12:59:00 为午休时间，不需要任何采样
                13:00:00-13:05:00 采样定义为13:05:00
                13:06:00-13:10:00 采样定义为13:10:00
                ...
                14:56:00-15:00:00 采样定义为15:00:00

            """  
            # 基础数据准备：获取全部证券代码
            df_all_code = security.get_all_code(self)
            #print(df_all_code)
            #第一部分：修正当日停盘数据
            df_tingpai = pro_api.suspend_k(self)
            #print(df_tingpai.query('suspend_timing == suspend_timing'))
            for index , row in df_tingpai.query('suspend_timing != suspend_timing').iterrows():
                code = row['code']
                date = row['date']
                suspend_type = row['suspend_type']
                if suspend_type == 'S':
                    #全天停牌，删除对应的一分钟线数据
                    count_query = text(f"SELECT COUNT(*) FROM akshare_1m WHERE code = '{code}' AND date(date) = '{date.date()}'")
                    sql_query = text(f"delete from akshare_1m where code = '{code}' and date(date) = '{date.date()}'")
                    try:
                        with self.engine.begin() as connection:
                            # 首先执行计数查询
                            count_result = connection.execute(count_query).scalar()
                            # 再执行删除操作
                            connection.execute(sql_query)
                            print(f"删除{code}|{date.date()} 成功，共删除{count_result}行数据！")
                    except exc.ResourceClosedError:
                        print(f"删除{code}|{date.date()} 失败！")
                elif suspend_type == 'R':    
                    pass    #复牌，不做任何处理
                else:
                    pass    #其他
            #第二部分：修正当日部分时段停盘数据
            print(df_tingpai.query('suspend_timing == suspend_timing'))
            # 第三部分：修复开盘价为0的数据
            
            for code in df_all_code['code']:
                # 3.1 按代码循环查询每个代码的开盘和交易日数据
                df_code_day_string = f"select date,open from akshare_1m where code = '{code}' and date between '{self.start_date}' and '{self.end_date}'"
                # 初始化1m并赋值
                df_1m = pd.DataFrame()
                df_1m = pd.read_sql_query(df_code_day_string, self.engine)
                if df_1m.empty:
                    print(f"代码 {code} 在指定日期范围内没有1分钟线数据，跳过修复")
                    continue
                # 收集开盘价为0的日期，聚合到日期
                df_open_zero_date = df_1m.query('open == 0')
                #print(f"代码 {code} 开盘价为0的日期：{df_open_zero_date['date'].dt.date.unique()}")
                # 3.2 按日进行修复
                for day in df_open_zero_date['date'].dt.date.unique():
                    # 获取当天1d的开盘价
                    open_price = pd.read_sql_query(f"select open from tspro_1d where code = '{code}' and date(date) = '{day}'", self.engine)
                    # open_price有数据则修复，否则报错
                    if open_price.empty or open_price['open'].values[0] == 0:
                        raise ValueError(f"{code} {day} 无法修复，开盘价无数据或为0")
                    else:
                        #print(f"正在修复代码 {code} 日期 {day} 的开盘价为0的数据，当日收盘价为{open_price['open'].values[0]}")
                        # 获取1m需要修复的当天数据
                        df_1m_today = pd.DataFrame()
                        df_1m_today = pd.read_sql_query(f"select id,code,date,open,close from akshare_1m where code = '{code}' and date(date) = '{day}' order by date asc", self.engine)
                        #print("##########修复前数据如下")
                        #print(df_1m_today)
                        # 3.3 修复逻辑
                        # 当天第一条open价格直接用1d的开盘价，其余open价格为前一根K线的close价格
                        df_1m_today.loc[df_1m_today.index[0], 'open'] = open_price['open'].values[0]
                        df_1m_today.loc[df_1m_today['open'] == 0, 'open'] = df_1m_today['close'].shift(1).fillna(df_1m_today['close'])
                        # 将修复后的数据更新回数据库
                        #通过mysql事务的方式，一次性更新全部need_fix = 1 的数据
                        #print("##########修复后数据如下")
                        #print(df_1m_today)
                        try:
                            with self.engine.begin() as connection:
                                #connection.begin()
                                for index, row in df_1m_today.iterrows():
                                    id = row['id']
                                    open_price = row['open']
                                    sql_update= text(f"update akshare_1m set open = {open_price} where id = {id}")
                                    connection.execute(sql_update)
                                connection.commit()
                                print(f"{day}|{code} 修正成功")
                        except:
                            with self.engine.begin() as connection:
                                connection.rollback()
                                print(f"{day}|{code} 修正失败，回滚数据")
            print("1分钟线修正完毕")

    def fix_1min_error_by_code_v3(self, day = datetime(2023,12,1)):
            """
            第三版的更新逻辑（对指定的代码进行修正）
            详见bug616：https://huiqiao.visualstudio.com/MyFunds/_workitems/edit/616
            【输入】
                start_date 默认无需输入
                end_date 默认无需输入
                code 默认无需输入

            """  
            code = self.code
            # 对指定代码和区间的数据进行修复
            df_code_day_string = f"select date,open from akshare_1m where code = '{code}' and date between '{self.start_date}' and '{self.end_date}'"
            # 初始化1m并赋值
            df_1m = pd.DataFrame()
            df_1m = pd.read_sql_query(df_code_day_string, self.engine)
            if df_1m.empty:
                print(f"代码 {code} 在指定日期范围内没有1分钟线数据，跳过修复")
                return
            # 收集开盘价为0的日期，聚合到日期
            df_open_zero_date = df_1m.query('open == 0')
            #print(f"代码 {code} 开盘价为0的日期：{df_open_zero_date['date'].dt.date.unique()}")
            # 3.2 按日进行修复
            for day in df_open_zero_date['date'].dt.date.unique():
                # 获取当天1d的开盘价
                open_price = pd.read_sql_query(f"select open from tspro_1d where code = '{code}' and date(date) = '{day}'", self.engine)
                # open_price有数据则修复，否则报错
                if open_price.empty or open_price['open'].values[0] == 0:
                    raise ValueError(f"{code} {day} 无法修复，开盘价无数据或为0")
                else:
                    #print(f"正在修复代码 {code} 日期 {day} 的开盘价为0的数据，当日收盘价为{open_price['open'].values[0]}")
                    # 获取1m需要修复的当天数据
                    df_1m_today = pd.DataFrame()
                    df_1m_today = pd.read_sql_query(f"select id,code,date,open,close from akshare_1m where code = '{code}' and date(date) = '{day}' order by date asc", self.engine)
                    #print("##########修复前数据如下")
                    #print(df_1m_today)
                    # 3.3 修复逻辑
                    # 当天第一条open价格直接用1d的开盘价，其余open价格为前一根K线的close价格
                    df_1m_today.loc[df_1m_today.index[0], 'open'] = open_price['open'].values[0]
                    df_1m_today.loc[df_1m_today['open'] == 0, 'open'] = df_1m_today['close'].shift(1).fillna(df_1m_today['close'])
                    # 将修复后的数据更新回数据库
                    #通过mysql事务的方式，一次性更新全部need_fix = 1 的数据
                    #print("##########修复后数据如下")
                    #print(df_1m_today)
                    try:
                        with self.engine.begin() as connection:
                            #connection.begin()
                            for index, row in df_1m_today.iterrows():
                                id = row['id']
                                open_price = row['open']
                                sql_update= text(f"update akshare_1m set open = {open_price} where id = {id}")
                                connection.execute(sql_update)
                            connection.commit()
                            print(f"{day}|{code} 修正成功")
                    except:
                        with self.engine.begin() as connection:
                            connection.rollback()
                            print(f"{day}|{code} 修正失败，回滚数据")
            print(f"{code} 1分钟线修正完毕")

    def fix_1min_error_v2(self, day = datetime(2023,12,1)):
        """
        目前采用第二版的更新逻辑
        自2025/4起东财做了更新限制，目前比较难获取5m数据，因此后续将会修改
        本模块使用5分钟线数据对1分钟线进行数据修正，目前存在以下几个问题：
        1. 当日停盘个股在1分钟线上是有数据的（成交量为0），如果隔日截取，则停盘日取不到1分钟数据；
        2. 如果对历史的1分钟数据进行截取，则开盘价open均为0（1分钟线数据仅保留5天）
        3. 当日临时停盘，未知

        【输入】
            start_date
            end_date

        """  
        raise ValueError(f'已移除该功能')
        #第一部分：修正当日停盘数据
        df_tingpai = pro_api.suspend_k(self)
        #print(df_tingpai.query('suspend_timing == suspend_timing'))
        for index , row in df_tingpai.query('suspend_timing != suspend_timing').iterrows():
            code = row['code']
            date = row['date']
            suspend_type = row['suspend_type']
            if suspend_type == 'S':
                #全天停牌，删除对应的一分钟线数据
                count_query = text(f"SELECT COUNT(*) FROM akshare_1m WHERE code = '{code}' AND date(date) = '{date.date()}'")
                sql_query = text(f"delete from akshare_1m where code = '{code}' and date(date) = '{date.date()}'")
                try:
                    with self.engine.begin() as connection:
                        # 首先执行计数查询
                        count_result = connection.execute(count_query).scalar()
                        # 再执行删除操作
                        connection.execute(sql_query)
                        print(f"删除{code}|{date.date()} 成功，共删除{count_result}行数据！")
                except exc.ResourceClosedError:
                    print(f"删除{code}|{date.date()} 失败！")
            elif suspend_type == 'R':    
                pass    #复牌，不做任何处理
            else:
                pass    #其他
        #第二部分：修正当日部分时段停盘数据
        print(df_tingpai.query('suspend_timing == suspend_timing'))

        #第三部分：开盘价Open为0的数据修正
        #3.1 查询日期段间的交易日
        df_trade_day = security.get_calendar(self)
        for day in df_trade_day['date']:    #循环读取每个交易日
            sql_code = f"select distinct code from akshare_60m where date(date) = '{day.date()}'"
            df_code = pd.read_sql_query(sql_code , self.engine)
            for code in df_code['code']:    #循环读取每个代码
                sql_1m_day = f"select date(date) as date , count(date) as num  from akshare_1m where date(date) ='{day.date()}' and code = '{code}' and open = 0 group by date(date)"
               
                df_1m_day = pd.read_sql_query(sql_1m_day , self.engine)
                #print(df_1m_day )
                if df_1m_day.empty == True:
                    #无数据，跳过
                    print(f"{day.date()}|{code} 无数据，跳过")
                else:
                    #有数据，进行修正
                    #注：这里推送过来的数据是akshare_1m中含open=0的日期，可能有1行也可能有多行
                    for day_need_fix in df_1m_day['date']:
                        df_1m = pd.read_sql_query(f"select id,code,date,open,close from akshare_1m where date(date) = '{day_need_fix}' and code = '{code}'" , self.engine)
                        df_60m = pd.read_sql_query(f"select id,code,date,open,close from akshare_60m where date(date) = '{day_need_fix}' and code = '{code}'" , self.engine)
                        if df_60m.empty == True:
                            raise ValueError(f"60分钟线{day_need_fix}|{code}无数据，无法修正")
                        else:
                            #将open = 0 的数据进行特别标注
                            df_1m.loc[df_1m['open'] == 0 , 'need_fix'] = 1
                            #获取需要修正的条目数
                            num_need_fix = df_1m.loc[df_1m['open'] == 0 , 'need_fix'].count()
                            #对df_1m第一根K线open价格进行修正
                            df_1m.loc[df_1m.index[0], 'open'] = df_60m.loc[df_60m.index[0], 'open']
                            #对df_1m其余K线进行修正，如果该行open价格为0，则取上一根K线的close价格
                            df_1m.loc[df_1m['open'] == 0 , 'open'] = df_1m['close'].shift(1).fillna(df_1m['close'])
                            #通过mysql事务的方式，一次性更新全部need_fix = 1 的数据
                            try:
                                with self.engine.begin() as connection:
                                    #connection.begin()
                                    for index, row in df_1m.query('need_fix == 1').iterrows():
                                        id = row['id']
                                        open_price = row['open']
                                        sql_update= text(f"update akshare_1m set open = {open_price} where id = {id}")
                                        connection.execute(sql_update)
                                    connection.commit()
                                    print(f"{day.date()}|{code} 修正成功，总计{num_need_fix}条")
                            except:
                                with self.engine.begin() as connection:
                                    connection.rollback()
                                    print(f"{day.date()}|{code} 修正失败，回滚数据")
        print("1分钟线修正完毕")
        #以下数据作为存档，已无作用
        # 从 akshare_60m 表中获取每天的第一根 K 线的 OPEN 价格
        """
        另一种查询方法报错：
        SELECT code, DATE(date) AS date, FIRST_VALUE(OPEN) OVER (PARTITION BY code, DATE(date) ORDER BY date) AS first_open
        FROM akshare_60m
        GROUP BY code, DATE(date)
        """
        #60分钟的内连接查询，用来修正无法进行group by操作的问题，这里保留
        sql_60m = f"""
            SELECT a.code, DATE(a.date) AS date, a.open
            FROM akshare_60m  a
            JOIN (
                SELECT code, DATE(date) AS date, MIN(date) AS min_date
                FROM akshare_60m where date between '{self.start_date}' and '{self.end_date}' 
                GROUP BY code, DATE(date)
            ) b ON a.code = b.code AND a.date = b.min_date
        """
    
    def fix_1min_error(self, day = datetime(2023,12,1)):
        """
        目前采用第二版的更新逻辑
        本模块需要修复的内容：
        1. 修复1分钟线历史数据开盘价格为0的问题
        2. 修复停牌当日1分钟线仍然有数据的情况
        详细描述参见task473
        输入：
            day 校验的起始日期，由于校验日期的第一条代码9:30的可能为0，所以需要前一天的数据
        V1版本修正逻辑：
            1. 取出sql_1d 按代码排列
            2. 取出1m的sql_code，按代码排列
            3. 按code进行循环
            3.1 查询1m详细数据
            3.2 查询60m详细数据
            3.3 1m fix_mode置0
            3.4 1m开盘价如果为0，则对矩阵fix_mode进行设置
            3.5 1m设置其余开盘价为0的数据为offset模式
            3.6 60分钟线中的数据open填充至1分钟线（每天4个K线的开盘价）
            3.7 对于offset的数据进行填充
            3.8 对fix_mode指定的几种类型（也就是填充过的），进行写回数据库操作
        """
        #1. 获取开始日期至今的全部代码
        #还有一种sql语句的处理方法是先取出open=0的数据，再group
        #优点：点断续传后，已修正的代码就不会重复计算，节约时间
        #缺点：会历遍整个数据库，目前大约需要耗时1分钟，将来会显著增加，而且如果当天没有更新完毕，后面一天的数据进来后，优势就不存在了，因为又需要从头开始进行修正
        #TO DO: 从其他渠道取得代码，然后进行修正
        raise ValueError(f'已移除该功能')
        sql_1d = f"select code from tspro_1d where date >= '{day}' group by code order by code"
        df_1d_code = pd.read_sql_query(sql_1d , self.engine)
        sql_code = 'select code from akshare_1m group by code' #2023/12/13查询耗时7秒
        df_code = pd.read_sql_query(sql_code , self.engine)
        print(df_code)
        for code in df_code['code']:
            #按照每个代码进行修正
            sql_1min = f"select id,code,date,open,close,volume from akshare_1m where code ='{code}' and date(date) >='{day.date()}'"
            sql_60min = f"select id,code,date,open,close,volume from akshare_60m where code ='{code}' and date(date) >='{day.date()}'"
            df_db_1min = pd.read_sql_query(sql_1min , self.engine)
            df_db_60min = pd.read_sql_query(sql_60min , self.engine)
            #df_db_1min['date'] = pd.to_datetime(df_db_1min['date'])
            #df_db_60min['date'] = pd.to_datetime(df_db_60min['date'])
            #默认修正模式为无需修正
            df_db_1min['fix_mode'] = 0  #这里如果修改成np.nan会导致后面的merge出错
            ###1. 构造1min矩阵
            #取出09:30 10:30 14:00 15:00的数据
            df_db_1min.loc[(df_db_1min.open == 0) & (df_db_1min.date.dt.time == datetime.strptime("09:30","%H:%M").time()), "fix_mode"] = '60min_mode1'
            df_db_1min.loc[(df_db_1min.open == 0) & (df_db_1min.date.dt.time == datetime.strptime("10:31","%H:%M").time()), "fix_mode"] = '60min_mode2'
            df_db_1min.loc[(df_db_1min.open == 0) & (df_db_1min.date.dt.time == datetime.strptime("13:01","%H:%M").time()), "fix_mode"] = '60min_mode2'
            df_db_1min.loc[(df_db_1min.open == 0) & (df_db_1min.date.dt.time == datetime.strptime("14:01","%H:%M").time()), "fix_mode"] = '60min_mode2'
            #设置其余开盘价为0的数据为offset模式
            df_db_1min.loc[(df_db_1min.open == 0) & (df_db_1min['fix_mode'] == 0), "fix_mode"] = 'offset'
            #初始化fix_date（分成两个模式，有不同的规则 +60和+59）
            df_db_1min.loc[(df_db_1min.fix_mode == '60min_mode1'), "fix_date"] = df_db_1min.loc[(df_db_1min.fix_mode == '60min_mode1'), "date"] + timedelta(minutes = 60)
            df_db_1min.loc[(df_db_1min.fix_mode == '60min_mode2'), "fix_date"] = df_db_1min.loc[(df_db_1min.fix_mode == '60min_mode2'), "date"] + timedelta(minutes = 59)
            #df_db_1min['fix_date'] = pd.to_datetime(df_db_1min['fix_date'])
            #print(df_db_1min.query("fix_mode in ['60min_mode1','60min_mode2']"))
            ####2. 60分钟线中的数据open填充至1分钟线
            df_db_1min = pd.merge(df_db_1min[['id','code','date','open','close','fix_date','fix_mode']], df_db_60min[['code', 'date','open']], left_on=['code', 'fix_date'], right_on=['code', 'date'], how='left')
            df_db_1min.loc[(df_db_1min.fix_mode == '60min_mode1'), "open_x"] = df_db_1min.loc[(df_db_1min.fix_mode == '60min_mode1'), "open_y"] 
            df_db_1min.loc[(df_db_1min.fix_mode == '60min_mode2'), "open_x"] = df_db_1min.loc[(df_db_1min.fix_mode == '60min_mode2'), "open_y"] 
            ####3. 对于offset的数据进行填充
            df_db_1min.loc[(df_db_1min.fix_mode == 'offset'), "open_x"] = df_db_1min['close'].shift(1).fillna(df_db_1m_today['close'])           
            df_db = df_db_1min[['id','code','date_x','open_x','close','fix_mode']]
            #df_db.to_csv('.\\data\\海龟模型\\1min_fix.csv', encoding = 'utf_8_sig')
            ####4. 重新写回数据库
            df_db = df_db_1min.query("fix_mode in ['60min_mode1','60min_mode2','offset']")
            db_count = df_db.shape[0]
            n = 1
            print(f'正在更新{code}')  #简略版
            for id in df_db['id']:
                open = df_db.loc[df_db.id == id].iloc[0].at['open_x']
                sql_update = text(f"update akshare_1m set open = {open} where id = {id}")
                try:
                    with self.engine.begin() as connection:
                        connection.execute(sql_update)
                        #print(f'正在更新{code}，已更新{n}/{db_count}')  #详细版
                        #print(f'正在更新{code}')  #简略版
                        pass
                except exc.ResourceClosedError: 
                    #提示信息暂时挪到外测，因为点断续传后，更新过的内容没有打印输出，因此会空白很久
                    print(f'更新{code}出现错误！')
                n += 1    

    def insert_cumulative_turnover(self):
        """
        继承和调用tspro同名函数
        """
        raise ValueError(f'已移除该功能')
        return tspro_data.insert_cumulative_turnover(self)

    def analyse_cumulative_turnover(self):
        """
        继承和调用tspro同名函数
        """
        raise ValueError(f'已移除该功能')
        return tspro_data.e_cumulative_turnover(self) 

    def resample_1m_to_60m(self, flash_to_database = False, show_timing=False):
        """
        将指定区间的1分钟K线重采样为特定4个时间点的60分钟K线
        默认返回60m的dataframe数据
        flash_to_database：将60m的差额数据写回数据库，默认不写入 为False
        备注：
            1. 目前不进行1m线与1d线的校验，也就是不能保证重采样的完整性
            2. 默认数据为不复权
        参数:
        df_1m: DataFrame，包含1分钟K线数据，至少需要包含以下列:
            - datetime: 日期时间列，为datetime类型
            - open: 开盘价
            - high: 最高价
            - low: 最低价
            - close: 收盘价
            - volume: 成交量
            - money: 成交额
            
        参数:
        flash_to_database: bool, 是否将数据写入数据库，默认为False
        show_timing: bool, 是否显示各步骤的耗时信息，默认为False
        
        返回:
        DataFrame: 重采样后的60分钟K线数据
        """
        func_start_time = time.time()
        if show_timing:
            print(f"{self.code} | 开始执行 resample_1m_to_60m...")
        
        self.fq = self.复权.不复权
        self.ktype = '1m'
        
        # 阶段1: 获取1分钟数据
        step1_start = time.time()
        df_1m = self.get_k_data()  # 获取1分钟K线数据
        step1_time = time.time() - step1_start
        if show_timing:
            print(f"{self.code} | 步骤1-获取1m数据耗时: {step1_time:.2f}秒")
        
        # 如果1m数据为空，则跳过
        if df_1m.empty:
            print(f"{self.code} | 1分钟K线数据为空，无法进行重采样！")
            return pd.DataFrame()
        self.ktype = '60m'  # 重置K线类型为60分钟
        #df_60m = self.get_k_data()  # 获取60分钟K线数据（用于对比）
        # df_1m 表头为 id	code	date	open	high	low	close	volume	money
        
        # 阶段2: 数据预处理
        step2_start = time.time()

        # 确保date列为索引且为datetime类型
        if 'date' in df_1m.columns:
            df_1m['date'] = pd.to_datetime(df_1m['date'])  # 确保date为datetime类型
            df_1m = df_1m.set_index('date')  # 设置date为索引
        
        # 创建交易日期列和时间列
        df_1m['trade_date'] = df_1m.index.date
        df_1m['time'] = df_1m.index.time
        step2_time = time.time() - step2_start
        if show_timing:
            print(f"{self.code} | 步骤2-数据预处理耗时: {step2_time:.2f}秒")
        
        # 阶段3: 定义时间段
        step3_start = time.time()
        # 定义4个时间段的结束时间点
        time_slots = {
            '10:30:00': ('09:30:00', '10:30:00'),
            '11:30:00': ('10:31:00', '11:30:00'),
            '14:00:00': ('13:00:00', '14:00:00'),
            '15:00:00': ('14:01:00', '15:00:00')
        }
        step3_time = time.time() - step3_start
        if show_timing:
            print(f"{self.code} | 步骤3-时间段定义耗时: {step3_time:.2f}秒")
        
        # 阶段4: 重采样计算
        step4_start = time.time()
        results = []
        
        # 按交易日分组处理
        for date, group in df_1m.groupby('trade_date'):
            for end_time, (start_time, end_time) in time_slots.items():
                # 转换为datetime.time对象进行比较
                start_time_obj = pd.to_datetime(start_time).time()
                end_time_obj = pd.to_datetime(end_time).time()
                
                # 筛选当前时间段的数据
                mask = (group.index.time >= start_time_obj) & (group.index.time <= end_time_obj)
                period_data = group[mask]
                
                if not period_data.empty:
                    # 创建重采样K线
                    new_row = {
                    'date': pd.Timestamp.combine(date, pd.to_datetime(end_time).time()),
                    'open': period_data['open'].iloc[0],
                    'high': period_data['high'].max(),
                    'low': period_data['low'].min(),
                    'close': period_data['close'].iloc[-1],
                    'volume': period_data['volume'].sum(),
                    'money': period_data['money'].sum(),
                    'trade_date': date
                    }
                    results.append(new_row)
        
        step4_time = time.time() - step4_start
        if show_timing:
            print(f"{self.code} | 步骤4-重采样计算耗时: {step4_time:.2f}秒")
        
        # 阶段5: 结果DataFrame创建
        step5_start = time.time()
        # 创建结果DataFrame
        df_resample_60m = pd.DataFrame(results)
        
        # 将datetime设置为索引
        if 'datetime' in df_resample_60m.columns:
            df_resample_60m = df_resample_60m.set_index('datetime')

        # 增加code列
        df_resample_60m['code'] = self.code        # 丢弃trade_date列
        if 'trade_date' in df_resample_60m.columns:
            df_resample_60m = df_resample_60m.drop(columns=['trade_date'])
            
        step5_time = time.time() - step5_start
        if show_timing:
            print(f"{self.code} | 步骤5-DataFrame创建耗时: {step5_time:.2f}秒")
        
        # 阶段6: 数据库操作（如果需要）
        if flash_to_database == True:    # 判断是否写回数据库
            step6_start = time.time()
            if show_timing:
                print(f"{self.code} | 开始数据库操作...")
            # 获取60m数据
            df_60m = self.get_k_data()
            
            # 如果数据库中没有60m数据，则直接写入所有重采样数据
            if df_60m.empty:
                df_diff = df_resample_60m.copy()
                print(f"{self.code} | 数据库中无60分钟K线数据，将写入全部重采样数据")
            else:
                # 比对差集
                df_diff = df_resample_60m[~df_resample_60m['date'].isin(df_60m['date'])]
            
            # 检查差集数据，删除open=0的全部行
            len_origin = len(df_diff)
            df_diff = df_diff[df_diff['open'] != 0]
            len_update = len(df_diff)
            #print(df_diff)
            # 将数据写回数据库
            if not df_diff.empty:
                df_diff.to_sql(
                        name = 'akshare_60m',
                        con = self.engine,
                        index = False,
                        if_exists = 'append')
                if len_origin == len_update:
                    print(f"{self.code} | 60分钟K线数据差集已写入数据库，总共{len_origin}条记录")
                else:
                    print(f"{self.code} | 60分钟K线数据差集含无效数据，扣除{len_origin - len_update}条后已写入数据库，总共{len_update}条记录")

            else:
                print(f"{self.code} | 60分钟K线数据无差集，无需写入数据库")
            
            step6_time = time.time() - step6_start
            if show_timing:
                print(f"{self.code} | 步骤6-数据库操作耗时: {step6_time:.2f}秒")
        else:  # 不写回，跳过
            pass       
        
        end_time = time.time()
        if show_timing:
            print(f"{self.code} | resample_1m_to_60m 执行完成，耗时: {end_time - func_start_time:.2f}秒")
        return df_resample_60m[['code', 'date', 'open', 'high', 'low', 'close', 'volume', 'money']]

    def resample_1m_to_5m(self, flash_to_database=False, show_timing=False):
        """
        将指定区间的1分钟K线重采样为5分钟K线
        按照中国股市的交易时间规则，生成48根5分钟K线
        
        时间区间规则：
        原始1m数据：上午09:30-11:30, 下午13:01-15:00（剔除09:30集合竞价）
        上午：09:31-09:35→09:35, 09:36-09:40→09:40, ..., 11:26-11:30→11:30 (共24根)
        下午：13:01-13:05→13:05, 13:06-13:10→13:10, ..., 14:56-15:00→15:00 (共24根)
        总计：48根5分钟K线
        
        默认返回5m的dataframe数据
        flash_to_database：将5m的差额数据写回数据库，默认不写入 为False
        
        参数:
        flash_to_database: bool, 是否将数据写入数据库
        show_timing: bool, 是否显示各步骤的耗时信息，默认为False
        
        返回:
        DataFrame: 重采样后的5分钟K线数据
        """
        import time
        func_start_time = time.time()
        if show_timing:
            print(f"{self.code} | 开始执行 resample_1m_to_5m...")
        
        # 设置复权方式和K线类型
        self.fq = self.复权.不复权
        self.ktype = '1m'
        
        # 阶段1: 获取1分钟数据
        step1_start = time.time()
        df_1m = self.get_k_data()  # 获取1分钟K线数据
        #print(df_1m)
        step1_time = time.time() - step1_start
        if show_timing:
            print(f"{self.code} | 步骤1-获取1m数据耗时: {step1_time:.2f}秒")
        
        # 如果1m数据为空，则跳过
        if df_1m.empty:
            print(f"{self.code} | 1分钟K线数据为空，无法进行重采样！")
            return pd.DataFrame()
            
        # 重置K线类型为5分钟
        self.ktype = '5m'
        
        # 阶段2: 数据预处理
        step2_start = time.time()
        # 确保date列为索引且为datetime类型
        if 'date' in df_1m.columns:
            df_1m['date'] = pd.to_datetime(df_1m['date'])
            df_1m = df_1m.set_index('date')
        
        # 剔除每天09:30的1分钟数据，使逻辑更清晰
        df_1m = df_1m[df_1m.index.time != pd.to_datetime('09:30:00').time()]
        
        # 创建交易日期列和时间列
        df_1m['trade_date'] = df_1m.index.date
        df_1m['time'] = df_1m.index.time
        step2_time = time.time() - step2_start
        if show_timing:
            print(f"{self.code} | 步骤2-数据预处理耗时: {step2_time:.2f}秒")
        
        # 阶段3: 定义时间区间
        step3_start = time.time()
        # 定义5分钟时间段的明确区间
        # 每个时间段定义为 (开始时间, 结束时间, 采样时间) 的元组
        time_intervals = []
        
        # 上午时间段：09:31-09:35, 09:36-09:40, ..., 11:26-11:30 (24根K线)
        # 09:31-09:35, 09:36-09:40, 09:41-09:45, 09:46-09:50, 09:51-09:55, 09:56-10:00
        # 10:01-10:05, 10:06-10:10, 10:11-10:15, 10:16-10:20, 10:21-10:25, 10:26-10:30
        # 10:31-10:35, 10:36-10:40, 10:41-10:45, 10:46-10:50, 10:51-10:55, 10:56-11:00
        # 11:01-11:05, 11:06-11:10, 11:11-11:15, 11:16-11:20, 11:21-11:25, 11:26-11:30
        morning_intervals = [
            ('09:31:00', '09:35:00'), ('09:36:00', '09:40:00'), ('09:41:00', '09:45:00'), ('09:46:00', '09:50:00'), ('09:51:00', '09:55:00'), ('09:56:00', '10:00:00'),
            ('10:01:00', '10:05:00'), ('10:06:00', '10:10:00'), ('10:11:00', '10:15:00'), ('10:16:00', '10:20:00'), ('10:21:00', '10:25:00'), ('10:26:00', '10:30:00'),
            ('10:31:00', '10:35:00'), ('10:36:00', '10:40:00'), ('10:41:00', '10:45:00'), ('10:46:00', '10:50:00'), ('10:51:00', '10:55:00'), ('10:56:00', '11:00:00'),
            ('11:01:00', '11:05:00'), ('11:06:00', '11:10:00'), ('11:11:00', '11:15:00'), ('11:16:00', '11:20:00'), ('11:21:00', '11:25:00'), ('11:26:00', '11:30:00')
        ]
        
        for start, end in morning_intervals:
            time_intervals.append((start, end, end))  # 采样时间为结束时间
        
        # 下午时间段：13:01-13:05, 13:06-13:10, ..., 14:56-15:00 (24根K线)
        # 13:01-13:05, 13:06-13:10, 13:11-13:15, 13:16-13:20, 13:21-13:25, 13:26-13:30
        # 13:31-13:35, 13:36-13:40, 13:41-13:45, 13:46-13:50, 13:51-13:55, 13:56-14:00
        # 14:01-14:05, 14:06-14:10, 14:11-14:15, 14:16-14:20, 14:21-14:25, 14:26-14:30
        # 14:31-14:35, 14:36-14:40, 14:41-14:45, 14:46-14:50, 14:51-14:55, 14:56-15:00
        afternoon_intervals = [
            ('13:01:00', '13:05:00'), ('13:06:00', '13:10:00'), ('13:11:00', '13:15:00'), ('13:16:00', '13:20:00'), ('13:21:00', '13:25:00'), ('13:26:00', '13:30:00'),
            ('13:31:00', '13:35:00'), ('13:36:00', '13:40:00'), ('13:41:00', '13:45:00'), ('13:46:00', '13:50:00'), ('13:51:00', '13:55:00'), ('13:56:00', '14:00:00'),
            ('14:01:00', '14:05:00'), ('14:06:00', '14:10:00'), ('14:11:00', '14:15:00'), ('14:16:00', '14:20:00'), ('14:21:00', '14:25:00'), ('14:26:00', '14:30:00'),
            ('14:31:00', '14:35:00'), ('14:36:00', '14:40:00'), ('14:41:00', '14:45:00'), ('14:46:00', '14:50:00'), ('14:51:00', '14:55:00'), ('14:56:00', '15:00:00')
        ]
        
        for start, end in afternoon_intervals:
            time_intervals.append((start, end, end))  # 采样时间为结束时间
        
        step3_time = time.time() - step3_start
        if show_timing:
            print(f"{self.code} | 步骤3-时间区间定义耗时: {step3_time:.2f}秒")
        
        # 阶段4: 重采样计算（终极优化版本）
        step4_start = time.time()
        
        # 预处理：转换时间区间为秒数，便于快速比较
        time_intervals_seconds = []
        for start_time, end_time, sample_time in time_intervals:
            start_seconds = pd.to_datetime(start_time).hour * 3600 + pd.to_datetime(start_time).minute * 60 + pd.to_datetime(start_time).second
            end_seconds = pd.to_datetime(end_time).hour * 3600 + pd.to_datetime(end_time).minute * 60 + pd.to_datetime(end_time).second
            sample_time_obj = pd.to_datetime(sample_time).time()
            time_intervals_seconds.append((start_seconds, end_seconds, sample_time_obj))
        
        # 使用列表推导式和向量化操作
        results = []
        
        # 按交易日分组处理
        for date, group in df_1m.groupby('trade_date'):
            # 预先计算时间的秒数，避免重复计算
            group_time_seconds = group.index.hour * 3600 + group.index.minute * 60 + group.index.second
            
            # 预先获取数据数组
            group_open = group['open'].values
            group_high = group['high'].values
            group_low = group['low'].values
            group_close = group['close'].values
            group_volume = group['volume'].values
            group_money = group['money'].values
            
            # 批量处理所有时间区间
            for start_seconds, end_seconds, sample_time_obj in time_intervals_seconds:
                # 使用numpy数组比较，速度更快
                mask = (group_time_seconds >= start_seconds) & (group_time_seconds <= end_seconds)
                
                if np.any(mask):  # 如果有匹配的数据
                    # 直接使用numpy数组操作
                    masked_open = group_open[mask]
                    masked_high = group_high[mask]
                    masked_low = group_low[mask]
                    masked_close = group_close[mask]
                    masked_volume = group_volume[mask]
                    masked_money = group_money[mask]
                    
                    results.append({
                        'date': pd.Timestamp.combine(date, sample_time_obj),
                        'open': masked_open[0],
                        'high': masked_high.max(),
                        'low': masked_low.min(),
                        'close': masked_close[-1],
                        'volume': masked_volume.sum(),
                        'money': masked_money.sum(),
                        'trade_date': date
                    })
        
        step4_time = time.time() - step4_start
        if show_timing:
            print(f"{self.code} | 步骤4-重采样计算耗时: {step4_time:.2f}秒")
        
        # 阶段5: 结果DataFrame创建
        step5_start = time.time()
        # 创建结果DataFrame
        df_resample_5m = pd.DataFrame(results)
        
        # 增加code列
        if not df_resample_5m.empty:
            df_resample_5m['code'] = self.code
            
            # 丢弃trade_date列
            if 'trade_date' in df_resample_5m.columns:
                df_resample_5m = df_resample_5m.drop(columns=['trade_date'])
                
        step5_time = time.time() - step5_start
        if show_timing:
            print(f"{self.code} | 步骤5-DataFrame创建耗时: {step5_time:.2f}秒")
        
        # 阶段6: 数据库操作（如果需要）
        if flash_to_database == True:  # 判断是否写回数据库
            step6_start = time.time()
            if show_timing:
                print(f"{self.code} | 开始数据库操作...")
            # 获取5m数据
            df_5m = self.get_k_data()
            
            # 如果数据库中没有5m数据，则直接写入所有重采样数据
            if df_5m.empty:
                df_diff = df_resample_5m.copy()
                print(f"{self.code} | 数据库中无5分钟K线数据，将写入全部重采样数据")
            else:
                # 比对差集
                df_diff = df_resample_5m[~df_resample_5m['date'].isin(df_5m['date'])]
            
            # 检查差集数据，删除open=0的全部行
            len_origin = len(df_diff)
            df_diff = df_diff[df_diff['open'] != 0]
            len_update = len(df_diff)
            
            # 将数据写回数据库
            if not df_diff.empty:
                df_diff.to_sql('akshare_5m', self.engine, if_exists='append', index=False)
                if len_origin == len_update:
                    print(f"{self.code} | 5分钟K线数据差集已写入数据库，总共{len_origin}条记录")
                else:
                    print(f"{self.code} | 5分钟K线数据差集含无效数据，扣除{len_origin - len_update}条后已写入数据库，总共{len_update}条记录")
            else:
                print(f"{self.code} | 5分钟K线数据无差集，无需写入数据库")
            
            step6_time = time.time() - step6_start
            if show_timing:
                print(f"{self.code} | 步骤6-数据库操作耗时: {step6_time:.2f}秒")
        
        end_time = time.time()
        if show_timing:
            print(f"{self.code} | resample_1m_to_5m 执行完成，耗时: {end_time - func_start_time:.2f}秒")
        return df_resample_5m[['code', 'date', 'open', 'high', 'low', 'close', 'volume', 'money']] if not df_resample_5m.empty else pd.DataFrame()

    def test_resample_5m_accuracy(self):
        """
        单元测试：验证5分钟重采样的准确性
        测试数据：300059.SZ 2025/7/1 - 2025/7/5
        预期结果：192条记录，第一条money=431319139.000，最后一条money=240238925.000
        """
        print("\n=== 开始5分钟重采样准确性测试 ===")
        
        # 设置测试参数
        original_code = self.code
        original_start = self.start_date
        original_end = self.end_date
        original_ktype = self.ktype
        
        try:
            # 设置测试数据
            self.code = '300059.SZ'
            self.start_date = datetime(2025, 7, 1)
            self.end_date = datetime(2025, 7, 5)
            
            # 执行重采样
            print(f"测试股票: {self.code}")
            print(f"测试时间范围: {self.start_date.date()} 到 {self.end_date.date()}")
            
            df_5m = self.resample_1m_to_5m(flash_to_database=False, show_timing=True)
            
            if df_5m.empty:
                print("❌ 测试失败：重采样结果为空")
                return False
            
            # 验证记录数量
            record_count = len(df_5m)
            expected_count = 192
            print(f"📊 实际记录数: {record_count}, 预期记录数: {expected_count}")
            
            if record_count != expected_count:
                print(f"⚠️ 警告：记录数量不匹配 (实际: {record_count}, 预期: {expected_count})")
            
            # 验证第一条记录的money
            if record_count > 0:
                first_money = df_5m.iloc[0]['money']
                expected_first_money = 431319139.000
                print(f"💰 第一条记录money: {first_money}, 预期: {expected_first_money}")
                
                if abs(first_money - expected_first_money) < 0.001:
                    print("✅ 第一条记录money验证通过")
                    first_test_pass = True
                else:
                    print("❌ 第一条记录money验证失败")
                    first_test_pass = False
            else:
                first_test_pass = False
            
            # 验证最后一条记录的money
            if record_count > 0:
                last_money = df_5m.iloc[-1]['money']
                expected_last_money = 240238925.000
                print(f"💰 最后一条记录money: {last_money}, 预期: {expected_last_money}")
                
                if abs(last_money - expected_last_money) < 0.001:
                    print("✅ 最后一条记录money验证通过")
                    last_test_pass = True
                else:
                    print("❌ 最后一条记录money验证失败")
                    last_test_pass = False
            else:
                last_test_pass = False
            
            # 显示测试结果详情
            print(f"\n📋 测试结果详情:")
            print(f"   - 数据时间范围: {df_5m['date'].min()} 到 {df_5m['date'].max()}")
            print(f"   - 总记录数: {record_count}")
            print(f"   - 第一条记录: {df_5m.iloc[0].to_dict()}" if record_count > 0 else "   - 第一条记录: 无数据")
            print(f"   - 最后一条记录: {df_5m.iloc[-1].to_dict()}" if record_count > 0 else "   - 最后一条记录: 无数据")
            
            # 综合测试结果
            all_tests_pass = (
                record_count == expected_count and 
                first_test_pass and 
                last_test_pass
            )
            
            if all_tests_pass:
                print("\n🎉 所有测试通过！5分钟重采样功能正常")
                return True
            else:
                print("\n⚠️ 部分测试未通过，请检查重采样逻辑")
                return False
                
        except Exception as e:
            print(f"\n💥 测试过程中发生错误: {e}")
            return False
            
        finally:
            # 恢复原始设置
            self.code = original_code
            self.start_date = original_start
            self.end_date = original_end
            self.ktype = original_ktype
            print(f"\n🔄 已恢复原始设置: {self.code}")

    def test_resample_60m_accuracy(self):
        """
        单元测试：验证60分钟重采样的准确性
        测试数据：300059.SZ 2025/7/1 - 2025/7/5
        预期结果：16条记录，第一条money=3039734046.000，最后一条money=2206680278.000
        """
        print("\n=== 开始60分钟重采样准确性测试 ===")
        
        # 设置测试参数
        original_code = self.code
        original_start = self.start_date
        original_end = self.end_date
        original_ktype = self.ktype
        
        try:
            # 设置测试数据
            self.code = '300059.SZ'
            self.start_date = datetime(2025, 7, 1)
            self.end_date = datetime(2025, 7, 5)
            
            # 执行重采样
            print(f"测试股票: {self.code}")
            print(f"测试时间范围: {self.start_date.date()} 到 {self.end_date.date()}")
            
            df_60m = self.resample_1m_to_60m(flash_to_database=False, show_timing=True)
            
            if df_60m.empty:
                print("❌ 测试失败：60分钟重采样结果为空")
                return False
            
            # 验证记录数量
            record_count = len(df_60m)
            expected_count = 16
            print(f"📊 实际记录数: {record_count}, 预期记录数: {expected_count}")
            
            if record_count != expected_count:
                print(f"⚠️ 警告：记录数量不匹配 (实际: {record_count}, 预期: {expected_count})")
            
            # 验证第一条记录的money
            if record_count > 0:
                first_money = df_60m.iloc[0]['money']
                expected_first_money = 3039734046.000
                print(f"💰 第一条记录money: {first_money}, 预期: {expected_first_money}")
                
                if abs(first_money - expected_first_money) < 0.001:
                    print("✅ 第一条记录money验证通过")
                    first_test_pass = True
                else:
                    print("❌ 第一条记录money验证失败")
                    first_test_pass = False
            else:
                first_test_pass = False
            
            # 验证最后一条记录的money
            if record_count > 0:
                last_money = df_60m.iloc[-1]['money']
                expected_last_money = 2206680278.000
                print(f"💰 最后一条记录money: {last_money}, 预期: {expected_last_money}")
                
                if abs(last_money - expected_last_money) < 0.001:
                    print("✅ 最后一条记录money验证通过")
                    last_test_pass = True
                else:
                    print("❌ 最后一条记录money验证失败")
                    last_test_pass = False
            else:
                last_test_pass = False
            
            # 显示测试结果详情
            print(f"\n📋 测试结果详情:")
            print(f"   - 数据时间范围: {df_60m['date'].min()} 到 {df_60m['date'].max()}")
            print(f"   - 总记录数: {record_count}")
            print(f"   - 第一条记录: {df_60m.iloc[0].to_dict()}" if record_count > 0 else "   - 第一条记录: 无数据")
            print(f"   - 最后一条记录: {df_60m.iloc[-1].to_dict()}" if record_count > 0 else "   - 最后一条记录: 无数据")
            
            # 综合测试结果
            all_tests_pass = (
                record_count == expected_count and 
                first_test_pass and 
                last_test_pass
            )
            
            if all_tests_pass:
                print("\n🎉 所有测试通过！60分钟重采样功能正常")
                return True
            else:
                print("\n⚠️ 部分测试未通过，请检查60分钟重采样逻辑")
                return False
                
        except Exception as e:
            print(f"\n💥 测试过程中发生错误: {e}")
            return False
            
        finally:
            # 恢复原始设置
            self.code = original_code
            self.start_date = original_start
            self.end_date = original_end
            self.ktype = original_ktype
            print(f"\n🔄 已恢复原始设置: {self.code}")

    def run_all_tests(self):
        """
        运行所有单元测试
        """
        print("🚀 开始运行所有单元测试...")
        
        test_results = []
        
        # 测试1: 5分钟重采样准确性
        result1 = self.test_resample_5m_accuracy()
        test_results.append(("5分钟重采样准确性", result1))
        
        # 测试2: 60分钟重采样准确性
        result2 = self.test_resample_60m_accuracy()
        test_results.append(("60分钟重采样准确性", result2))
        
        # 汇总结果
        print("\n" + "="*50)
        print("📊 单元测试结果汇总:")
        print("="*50)
        
        passed_count = 0
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name}: {status}")
            if result:
                passed_count += 1
        
        total_tests = len(test_results)
        print(f"\n总计: {passed_count}/{total_tests} 个测试通过")
        
        if passed_count == total_tests:
            print("🎉 所有测试通过！重采样功能正常运行")
        else:
            print("⚠️ 部分测试失败，建议检查相关功能")
        
        return passed_count == total_tests

    def data_prepare_task101(self) -> pd.DataFrame:
        """
        task101: 数据预处理任务 akshare 1m->5m重采样
        key: task101
        存储方式：Redis List
        数据类型："code": "300679.SZ", "start_date": "2025-07-10 08:00:00", "end_date": "2025-07-14 18:55:26"
                
        """
        # 基础数据准备：获取全部证券代码
        df_all_code = security.get_all_code(self)
        # 仅留下code列
        df_all_code = df_all_code[['code']]
        # 增加开始时间和结束时间列
        df_all_code['start_date'] = self.start_date
        df_all_code['end_date'] = self.end_date
        return df_all_code

    def task_process_task101(self):
        """
        多任务处理，从redis读取task101键值，进行重采样任务
        支持5线程同时处理
        
        线程安全说明：
        - 每个线程创建独立的data实例，避免实例变量互相干扰
        - 使用线程安全的queue进行任务分发
        - 使用锁保护共享的统计变量
        """
        import threading
        import queue
        import traceback
        import json
        from datetime import datetime
        
        print("############正在处理task101重采样任务###########")

        # 获取Redis连接
        rds = redisClient()
        rds_conn = rds.client  # 修复：client是属性，不是方法
        
        # 检查队列是否存在且有数据
        if not rds_conn.exists('task101') or rds_conn.llen('task101') == 0:
            print("task101队列不存在或为空，无任务需要处理")
            return

        # 获取队列长度
        queue_length = rds_conn.llen('task101')
        print(f"队列中共有{queue_length}个任务待处理")

        # 创建线程安全的队列用于任务分发
        task_queue = queue.Queue()
        
        # 方案1：一次性取出所有任务（当前方案 - 速度快但有风险）
        # 优点：处理速度快，减少Redis访问
        # 缺点：程序崩溃可能丢失任务
        print("正在从Redis获取任务...")
        while rds_conn.llen('task101') > 0:
            task_data = rds_conn.lpop('task101')  # 消费性操作：取出并删除
            if task_data is None:
                break
            task_queue.put(task_data)
        
        print(f"已从Redis获取{task_queue.qsize()}个任务，Redis队列现在为空（这是正常的）")
        
        # 统计变量（线程安全）
        stats_lock = threading.Lock()
        processed_count = 0
        error_count = 0
        
        def worker_thread():
            """
            工作线程函数
            每个线程创建独立的data实例，确保线程安全
            """
            nonlocal processed_count, error_count
            
            while True:
                try:
                    # 从队列获取任务（超时5秒）
                    task_data = task_queue.get(timeout=5)
                    if task_data is None:
                        break
                    
                    # 解析任务数据
                    if isinstance(task_data, bytes):
                        task_json = json.loads(task_data.decode('utf-8'))
                    else:
                        task_json = json.loads(task_data)
                    
                    code = task_json['code']
                    start_date = datetime.strptime(task_json['start_date'], '%Y-%m-%d %H:%M:%S')
                    end_date = datetime.strptime(task_json['end_date'], '%Y-%m-%d %H:%M:%S')
                    
                    print(f"线程{threading.current_thread().name}: 正在处理任务 {code} ({start_date.date()} 到 {end_date.date()})")
                    
                    # 关键点：为每个线程创建独立的数据处理实例
                    # 这确保了不同线程之间的code, start_date, end_date, ktype等变量不会互相干扰
                    worker_instance = data(myauth=True)
                    worker_instance.code = code
                    worker_instance.start_date = start_date
                    worker_instance.end_date = end_date
                    
                    # 执行1分钟到5分钟的重采样
                    df_5m = worker_instance.resample_1m_to_5m(flash_to_database=True, show_timing=False)
                    
                    # 线程安全地更新统计
                    with stats_lock:
                        processed_count += 1
                    
                    print(f"线程{threading.current_thread().name}: 任务完成 {code} - 生成{len(df_5m)}条5分钟K线数据")
                    
                except Exception as e:
                    # 线程安全地更新错误统计
                    with stats_lock:
                        error_count += 1
                    print(f"线程{threading.current_thread().name}: 任务处理失败 {code if 'code' in locals() else '未知'} - 错误: {str(e)}")
                    traceback.print_exc()
                finally:
                    # 标记任务完成
                    task_queue.task_done()
        
        # 创建并启动5个工作线程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_thread, name=f"Worker-{i+1}")
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        print(f"已启动5个工作线程，开始处理{queue_length}个任务...")
        
        # 等待所有任务完成
        task_queue.join()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        print(f"############task101重采样任务处理完成###########")
        print(f"成功处理: {processed_count}个任务")
        print(f"失败任务: {error_count}个")

    def task_process_task101_safe(self):
        """
        更安全的任务处理方案：逐个消费Redis任务
        优点：不会因程序崩溃而丢失任务
        缺点：Redis访问频率较高
        """
        import threading
        import traceback
        import json
        from datetime import datetime
        
        print("############正在处理task101重采样任务（安全模式）###########")

        # 获取Redis连接
        rds = redisClient()
        rds_conn = rds.client
        
        # 检查队列是否存在且有数据
        if not rds_conn.exists('task101') or rds_conn.llen('task101') == 0:
            print("task101队列不存在或为空，无任务需要处理")
            return

        # 获取初始队列长度
        initial_queue_length = rds_conn.llen('task101')
        print(f"队列中共有{initial_queue_length}个任务待处理")

        # 统计变量（线程安全）
        stats_lock = threading.Lock()
        processed_count = 0
        error_count = 0
        redis_lock = threading.Lock()  # Redis访问锁
        
        def worker_thread_safe():
            """
            安全的工作线程函数：直接从Redis消费任务
            """
            nonlocal processed_count, error_count
            
            while True:
                task_data = None
                try:
                    # 线程安全地从Redis获取任务
                    with redis_lock:
                        if rds_conn.llen('task101') > 0:
                            task_data = rds_conn.lpop('task101')
                        else:
                            break  # 队列为空，退出
                    
                    if task_data is None:
                        break
                    
                    # 解析任务数据
                    if isinstance(task_data, bytes):
                        task_json = json.loads(task_data.decode('utf-8'))
                    else:
                        task_json = json.loads(task_data)
                    
                    code = task_json['code']
                    start_date = datetime.strptime(task_json['start_date'], '%Y-%m-%d %H:%M:%S')
                    end_date = datetime.strptime(task_json['end_date'], '%Y-%m-%d %H:%M:%S')
                    
                    print(f"线程{threading.current_thread().name}: 正在处理任务 {code} ({start_date.date()} 到 {end_date.date()})")
                    
                    # 为每个线程创建独立的数据处理实例
                    worker_instance = data(myauth=True)
                    worker_instance.code = code
                    worker_instance.start_date = start_date
                    worker_instance.end_date = end_date
                    
                    # 执行1分钟到5分钟的重采样
                    df_5m = worker_instance.resample_1m_to_5m(flash_to_database=True, show_timing=False)
                    
                    # 线程安全地更新统计
                    with stats_lock:
                        processed_count += 1
                    
                    print(f"线程{threading.current_thread().name}: 任务完成 {code} - 生成{len(df_5m)}条5分钟K线数据")
                    
                except Exception as e:
                    # 如果处理失败，将任务放回队列（可选）
                    if task_data is not None:
                        with redis_lock:
                            rds_conn.rpush('task101_failed', task_data)  # 放入失败队列
                    
                    # 线程安全地更新错误统计
                    with stats_lock:
                        error_count += 1
                    print(f"线程{threading.current_thread().name}: 任务处理失败 {code if 'code' in locals() else '未知'} - 错误: {str(e)}")
                    traceback.print_exc()
        
        # 创建并启动5个工作线程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_thread_safe, name=f"SafeWorker-{i+1}")
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        print(f"已启动5个工作线程，开始处理{initial_queue_length}个任务...")
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        print(f"############task101重采样任务处理完成（安全模式）###########")
        print(f"成功处理: {processed_count}个任务")
        print(f"失败任务: {error_count}个")
        
        # 检查是否有失败的任务
        if rds_conn.exists('task101_failed'):
            failed_count = rds_conn.llen('task101_failed')
            print(f"失败任务已存储在task101_failed队列中，共{failed_count}个")
        
if __name__ == "__main__":
    # 测试项目1：使用ak数据源，获取日线数据
    akdata = data()  # 这里的data默认本地data源，是akdata
    akdata.code = '502010.SH'
    akdata.start_date = datetime(2024, 11, 4, 8)
    akdata.end_date = datetime(2025,12 , 15, 18)
    akdata.fq = akdata.复权.不复权
    akdata.fix_1min_error_by_code_v3()
    akdata.ktype = '1d'
    akdata.task_process_task101()  # 执行重采样任务处理
    # 测试项目2：重采样功能测试
    print("开始重采样功能测试...")
    akdata.ktype = '1m'
    df_1m = akdata.get_k_data()
    
    # 测试5分钟重采样
    df_5m = akdata.resample_1m_to_5m(flash_to_database=True, show_timing=True)
    print(f"5分钟重采样结果：{len(df_5m)}条记录")
    
    # 测试60分钟重采样
    df_60m = akdata.resample_1m_to_60m(flash_to_database=True, show_timing=True)
    print(f"60分钟重采样结果：{len(df_60m)}条记录")
    
    # 测试项目3：运行完整单元测试套件
    print("\n" + "="*60)
    print("开始运行单元测试套件...")
    print("="*60)
    akdata.run_all_tests()
