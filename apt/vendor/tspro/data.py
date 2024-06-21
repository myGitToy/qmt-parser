import numpy as np
import pandas as pd
import tushare as ts
import sqlalchemy
import akshare as ak
from sqlalchemy import create_engine,exc,delete,text   #用来捕捉sqlalchemy的异常
from datetime import datetime,timedelta
from apt.vendor.tspro.security import security  as security
from apt.vendor.tspro.base import base as base
from apt.vendor.tspro.base import stock as stock
from apt.vendor.tspro.security import security

#from apt.vendor.tspro.security import get_calendar

class data(base,stock):
    """
    数据接口 基类
    所有需要从tusharePro获取数据的都需要从此处引用
    引用规范：from apt.vendor.tspro.data import data as ts_data
    例：量化选股 qsp_jqdata就是从这里作为基类引用的
    要更改数据源，只需要更改此处的引用即可，范例如下
    a = ts_data(rds_host = ts_data.数据源.aliyun , myauth = False)
    """
    """
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
            query = f"select date , count(date) as num from tspro_{self.ktype} where date(date) = '{day.date()}'"
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
                    #差集处理
                    query = f"select code , date from tspro_{self.ktype} where date(date) = '{day.date()}'"
                    df_db = pd.read_sql_query(query , self.engine)
                    df_db['date'] = pd.to_datetime(df_db['date'])
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
                    print("%s 当日数据为空，跳过上传" % (day.strftime('%Y%m%d')))
                else:
                    df.to_sql(
                            name = f'tspro_{self.ktype}',
                            con = self.engine,
                            index = False,
                            if_exists = 'append')
                    print(f"{day.strftime('%Y%m%d')}数据已上传完成({self.ktype})")

    def update_day_ETF(self):
        """
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
            df = pd.concat([df , df_db , df_db] ).drop_duplicates(subset=['code','date'] , keep = False)
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

    def update_sequence_add(self , code_list = None , myclass = 'stock' , type = '60m'  , priority = 0 ):
        '''
        task346更改了分时线数据更新的逻辑，拆分成add和launch两部分
        add模块主要进行数据更新任务的导入
        输入：
            code_list 需要更新的证券代码列表，有列表（优先更新）和无列表（正常更新）进入的是两个不同的流程
            myclass 一级目录 默认stock  目前可接受参数stock|etf
            type 二级目录 默认60m；目前可接受参数：60m/1m
            priority 优先更新标识 默认为0
            此处未作auto_update的适配，因为目前tspro无分时权限，因此维持手动更新
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
                    df_main = df_main.append(record , ignore_index = True)
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
                    name = f'tspro_update_sequence',
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
            if type not in ['1d','60m','1m']:
                raise ValueError(f'无效的数据类型(二级目录)')
            #分时线类型校验
            if self.ktype == '1d' or type == '1d':
                raise ValueError(f'日线数据请使用update_day函数进行更新')
            #点断续传数据库条目数校验
            sql_count = 'select count(id) as count from tspro_update_sequence'
            df_db = pd.read_sql_query(sql_count , self.engine)
            if df_db.iloc[0].at['count'] == 0:
                #数据库不存在数据
                result = '1'
            else:
                #数据库存在数据，进行选择
                result = input('''数据库存在数据，请选择更新方式 \n
                1. 保留原有更新序列，添加新的序列 \n
                2. 删除原有更新序列，添加新的序列 \n
                3. 删除原有更新序列 \n
                4. 退出（不做任何处理）\n''')
            #无论数据库是否存在数据，到这里进行选择
            #无数据的直接进入1，有数据的按选择进行跳转
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
                        name = f'tspro_update_sequence',
                        con = self.engine,
                        index = False,
                        if_exists = 'append')
                print(f"上传已完成，新增{code_list.shape[0]}条更新序列！")

            elif result == '2':             #删除后添加
                sql_count = 'delete from tspro_update_sequence'
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
                        name = f'tspro_update_sequence',
                        con = self.engine,
                        index = False,
                        if_exists = 'append')
                print(f"上传已完成，新增{code_list.shape[0]}条更新序列！")

            elif result == '3':             #直接删除
                sql_count = 'delete from tspro_update_sequence'
                try:
                    with self.engine.begin() as connection:
                        connection.execute(sql_count)
                except exc.ResourceClosedError:
                    print(f"删除更新序列失败！")
                    
            elif result == '4':          #不做任何更改，直接跳出
                return 
            else:
                raise ValueError(f'无效的输入')

    def update_sequence_launch(self , priority = 0 ):
        '''
        task346更改了分时线数据更新的逻辑，拆分成add和launch两部分
        launch模块主要进行数据更新任务，支持点断续传
        priority 是否优先更新 默认为0
        '''
        #处理是否优先更新
        if priority == 1:
            #优先更新
            sql = "select * from tspro_update_sequence where priority = 1" 
        else:
            #没有优先更新列表 全部加载
            sql = "select * from tspro_update_sequence" 
        df_sequence = pd.read_sql_query(sql , self.engine)
        code_list = df_sequence['code']
        if df_sequence.shape[0] > 0 :
            #有数据，进行更新
            #设定最大更新行数
            max_row = 8000
            for index , row in df_sequence.iterrows():
                id = row['id']
                code = row['code']
                #start_date = datetime.strftime(row['start_date'] , '%Y-%m-%d')
                #end_date  = datetime.strftime(row['end_date'] , '%Y-%m-%d')
                start_date = row['start_date']
                end_date  = row['end_date']
                myclass = row['class']
                type = row['type']
                #tspro pro_bar数据获取模块（这里对最后日期做了day+1的处理）
                if myclass == 'stock':
                    df_tspro = ts.pro_bar(api = self.api , ts_code = code, freq = self.dict[type] , adj = None , start_date = start_date.strftime('%Y%m%d') , end_date = (end_date + timedelta(days = 1)).strftime('%Y%m%d') , adjfactor = True , factors = ['tor', 'vr'] , asset = 'E')
                elif myclass == 'etf':
                    df_tspro = ts.pro_bar(api = self.api , ts_code = code, freq = self.dict[type] , adj = None , start_date = start_date.strftime('%Y%m%d') , end_date = (end_date + timedelta(days = 1)).strftime('%Y%m%d') , adjfactor = True , asset = 'FD')
                #print(df_tspro)
                #最大数据量校验
                if df_tspro.shape[0] >= max_row:
                    raise ValueError(f'接收到的数据达到最大允许值，可能存在数据丢失，中止更新！')
                df_tspro.rename(columns={"ts_code": "code", "trade_time": "date" ,"vol" : "volume" , "amount" : "money"} , errors="raise" , inplace = True)
                #stock更新正常的，etf更新会报错
                if myclass == 'stock':
                    df_tspro.drop(columns = ['trade_date','pre_close'] , inplace = True)
                #时间日期类的列进行类型变更
                df_tspro['date'] = pd.to_datetime(df_tspro['date'])
                #日期排序(目前判定下为非必要，预留代码，减小数据更新的压力)
                #df_tspro.sort_values(columns = ['date'], inplace = True , ascending = False)
                #分时线数据不需要进行成交量和成交额修正
                #4. 获取数据库对应日期的数据
                query_db = f"select code,date,open,close,high,low,volume,money from tspro_{type} where date(date) between '{start_date.date()}' and '{end_date.date()}' and code = '{code}'"
                df_db = pd.read_sql_query(query_db , self.engine)
                df_db['date'] = pd.to_datetime(df_db['date'])
                #测试两个df格式
                #print(df_tspro)
                #print(df_db)
                #5. 两个DataFrame进行差值处理
                df_diff = pd.concat([df_tspro , df_db , df_db] ).drop_duplicates(subset=['date'] , keep = False)
                #6. 差值数据写入数据库
                if df_diff.empty == True:
                    print(f"{code}差值数据为空，跳过更新")
                else:
                    df_diff.to_sql(
                            name = f'tspro_{type}',
                            con = self.engine,
                            index = False,
                            if_exists = 'append')
                    print(f"{code}数据已上传完成({type}，新增数据{df_diff.shape[0]})")
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
                sql_delete = text(f"delete from tspro_update_sequence where id = {id}")
                try:
                    with self.engine.begin() as connection:
                        connection.execute(sql_delete)
                except exc.ResourceClosedError:
                    print(f"删除{code}更新序列失败！")
                    pass      
        else:
            #无数据，跳过
            print("更新序列无数据，跳过更新")

    def update_min(self):
        """
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
            df_db = pd.read_sql_query(query_db , self.engine)
            df_db['date'] = pd.to_datetime(df_db['date'])
            #print(df_tspro)
            #5. 两个DataFrame进行差值处理
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
            query = f"select date , count(date) as num from tspro_factor where date(date) = '{day.date()}'"
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
            其余模式end_date均为基准日期
            详见https://huiqiao.visualstudio.com/MyFunds/_workitems/edit/296
        flag_resample：T/F 用于标识是否进行重采样 60分钟线目前无法重采样，因为默认按照整点小时划分
            目前仅对60分钟线有效
            True：进行重采样
            False：不进行重采样，舍弃9:30单根数据
        接受前复权 后复权 不复权 动态复权四种复权模式
        成交量、成交额目前未进行复权处理
        返回的数据按照升序排列（backtrader要求的数据格式）
        """
        if self.start_date  > self.end_date:
            raise ValueError(f'开始日期必须早于结束日期')
        if self.ktype not in ['1d','1m','5m','30m','60m']:
            raise ValueError(f'不合规的K线类型: {self.ktype}')
        if self.code == None :
            raise ValueError(f'证券代码不能为空')
        if self.ktype == '1d':
            query = f"select * from tspro_{self.ktype} where code = '{self.code}' and date BETWEEN '{self.start_date.date()}' and '{self.end_date.date()}' order by date asc"
        else:
            query = f"select * from tspro_{self.ktype} where code = '{self.code}' and date BETWEEN '{self.start_date}' and '{self.end_date}' order by date asc"         
        df_db = pd.read_sql_query(query , self.engine)
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
            #print(df_db)
            #复权因子与K线数据进行拼接（复权因子和K线数据只有要一处空值，最后拼接的数据就会有所缺失 BUG 554修复此错误）
            df_db = pd.merge(df_db, tspro_factor[['factor_date','factor']] , on = ['factor_date'] , how = 'left')            
            #复权因子修正完毕，填充后进入复权处理
            #tspro每天均有复权因子，理论无需填充，但有时复权数据会不完整，因此依旧需要填充
            # 首先检查并填充最上方的缺失值为1.0
            df_db.iloc[0] = df_db.iloc[0].fillna(1.0)
            # 再次进行填充缺失值
            df_db.ffill(axis=0, inplace=True, limit=None) #此处移除downcast=None的参数
            #print(df_db)
            #进行60分钟线修正
            if self.ktype =='60m':
                #判断使用何种方式进行60分钟线修正
                if flag_resample == False:
                    #去除9：30数据
                    #df_db = df_db.drop(df_db[df_db['date'].dt.time == '09:30:00'].index)
                    #取出09:30数据
                    df_drop = df_db.query('date.dt.time == datetime.strptime("09:30","%H:%M").time()')
                    #两者取差集
                    df_db = pd.concat([df_db , df_drop , df_drop] ).drop_duplicates(subset=['date'] , keep = False)
                else:
                    #重采样
                    raise ValueError('暂不支持重采样')
                    df_db['date'] = pd.to_datetime(df_db['date'])
                    df_db.set_index('date',inplace = True)
                    df_db = df_db.resample('60min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum','money':'sum','factor':'first'}).dropna(axis=0)
                    print(df_db)

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

    def get_p_data(self, f_share = True , col_p = {"0.25": 'p25', "0.5": 'p50', "0.75": 'p75'}):
        """
        获取包含全换手区间的K线数据
        有四种不同的选择：1d/1m/全换手（全股）/全换手（自由流通盘）
        【输入】
            get_k_data 只能采用默认参数，无法进行自定义参数输入
            f_share 是否输出自由流通盘 True自由流通盘 False 总股本（如果是全流通的股票，则不影响）
            col：需要的分位数和列名
        """
        #导入模块（为了避免循环引用）
        from apt.vendor.tspro.cumulative_turnover import cum_turnover as ctr
        #初始化
        ###1. 根据选择的K线类型不同，进行不同级别的校验
        a = ctr()
        a.code = self.code
        a.start_date = self.start_date
        a.end_date = self.end_date
        a.ktype = self.ktype
        a.复权 = self.复权
        ##1.1 数据校验环节（如果数据缺失，则进入更新环节，未缺失才能进去后续的获取数据环节）
        if self.ktype == '1d':
            #校验1d数据
            a.update_price_range_1d_by_code()
        elif self.ktype == '1m':
            #校验1m数据
            raise ValueError(f'1m数据暂不支持全换手区间')
        else:
            raise ValueError(f'不支持的K线类型，请检查！')
        ###2. K线数据获取环节（不包含分位数信息）
        df_k = self.get_k_data()
        ###3. 数据处理和拼接环节
        #设定全流通列名
        if f_share == True:
            f_share_name = 'price_range_1d_f'
            f_share_days = 'turnover_days_f'    #增加输出全换手天数
            f_turnover_date = 'turnover_date_f' #增加输出全换手对应的日期
        else:
            f_share_name = 'price_range_1d'
            f_share_days = 'turnover_days'
            f_turnover_date = 'turnover_date'
        #取出col_p的全部键值
        col_p_list = list(col_p.keys())
        #取出col_p的全部名称
        col_p_name = list(col_p.values())
        #sql 语句范例SELECT code, date, price_range_1d_f->'$."0.25"' AS p25 FROM stock.tspro_cumulative_turnover
        #将键值转换成sql语句
        col_p_sql = ','.join([f"{f_share_name}->'$.\"{i}\"' AS {col_p[i]}" for i in col_p_list])
        #print(col_p_sql)
        #sql语句
        sql = f"SELECT code, date, {f_share_days} , {f_turnover_date} , {col_p_sql} FROM stock.tspro_cumulative_turnover where code = '{self.code}' and date(date) between '{self.start_date.date()}' and '{self.end_date.date()}'"
        #print(sql)
        df_p = pd.read_sql_query(sql , self.engine)
        #将df_p 拼接到df_k并最终输出
        df_k = pd.merge(df_k , df_p , on = ['code','date'] , how = 'left')
        return df_k

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
            其余模式end_date均为基准日期
            详见https://huiqiao.visualstudio.com/MyFunds/_workitems/edit/296
        接受前复权 后复权 不复权 动态复权四种复权模式
        成交量、成交额目前未进行复权处理
        返回的数据按照升序排列（backtrader要求的数据格式）
        """
        if self.start_date  > self.end_date:
            raise ValueError(f'开始日期必须早于结束日期')
        if self.ktype not in ['1d','1m','5m','30m','60m']:
            raise ValueError(f'不合规的K线类型: {self.ktype}')
        if self.code == None :
            raise ValueError(f'证券代码不能为空')
        if self.ktype == '1d':
            query = f"select * from tspro_{self.ktype} where code = '{self.code}' and date BETWEEN '{self.start_date.date()}' and '{self.end_date.date()}' order by date asc"
        else:
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

    def update_cumulative_turnover2(self):
        """
        更新累计换手率入库
        """
        raise ValueError('已移除该功能')
        df_basic = pd.read_sql_query(f"select code,date from tspro_basic force index (date) where date between '{self.start_date.date()}' and '{self.end_date.date()}'" , self.engine)
        df_cumulative_turnover = pd.read_sql_query(f"select code,date from tspro_cumulative_turnover force index (date) where date between '{self.start_date.date()}' and '{self.end_date.date()}'" , self.engine)
        df_db = pd.concat([df_basic, df_cumulative_turnover]).drop_duplicates(subset=['code','date'], keep=False)
        # Get rows from df_basic that are not in df_cumulative_turnover
        #df_missing_rows = df_basic[~df_basic[['code', 'date']].isin(df_cumulative_turnover[['code', 'date']])].dropna()
        #保存至数据库
        if df_db.empty == True:
            print("差集为空，跳过写入数据库")
        else:
            df_db.to_sql(
                    name = f'tspro_cumulative_turnover',
                    con = self.engine,
                    index = False,
                    if_exists = 'append')
            print(f"数据上传完成(tspro_cumulative_turnover)|新增数据{df_db.shape[0]}")
    def __sql_execute_time2(self , sql):
        """
        执行SQL语句
        """
        # 记录开始时间
        start_time = datetime.now()

        # 执行SQL语句
        df = pd.read_sql_query(sql , self.engine)
        # 记录结束时间
        end_time = datetime.now()
        # 计算并打印执行时间
        execution_time = end_time - start_time
        print(f"SQL execution time: {execution_time}")
        return df

    def analyse_cumulative_turnover2(self):
        """
        更新和分析累计换手率
        目前需要更新turnover_date,turnover_date_f这两个字段
        """
        sql_basic = f"select code,date,turnover_rate,turnover_rate_f from tspro_basic FORCE INDEX(main) where date between '{self.start_date.date()}' and '{self.end_date.date()}'"
        print(sql_basic)
        df_basic = self.__sql_execute_time(sql_basic)
        df_cumulative_turnover = self.__sql_execute_time(f"select code,date,turnover_valid from tspro_cumulative_turnover FORCE INDEX(main) where date between '{self.start_date.date()}' and '{self.end_date.date()}'" )
        #df_cumulative_turnover = pd.read_sql_query(f"select code,date,turnover_valid from tspro_cumulative_turnover force index(date) where date between '{self.start_date.date()}' and '{self.end_date.date()}'" , self.engine)
        df_cum_na = df_cumulative_turnover[df_cumulative_turnover['turnover_valid'].isnull()]
        #历遍df_cum_na
        for index , row in df_cum_na.iterrows():
            code = row['code']
            e_date = row['date']
            for n in [100,300,500,1000,5000]:
                s_date = e_date - timedelta(days = n)
                #df_db为tspro_basic数据查询中以e_date为基准的数据，降序排列
                df_db = pd.read_sql_query(f"select code,date,turnover_rate,turnover_rate_f from tspro_basic where code = '{code}' and date between '{s_date}' and '{e_date}'" , self.engine).sort_values('date', ascending=False)
                #数据条目的最后一个日期，用来进行比较
                last_date = df_db.iloc[-1]['date']
                #计算换手率累计值
                df_db['cum_turnover'] = df_db['turnover_rate'].cumsum()
                df_db['cum_turnover_f'] = df_db['turnover_rate_f'].cumsum()
                #需要df_db累加后的turnover_rate和turnover_rate_f均大于100                
                if df_db.query('cum_turnover >= 100').empty == False and df_db.query('cum_turnover_f >= 100').empty == False:
                    #累加值超过100，数据有效
                    turnover_date = df_db[df_db['cum_turnover'] >= 100].iloc[0]['date']
                    turnover_date_f = df_db[df_db['cum_turnover_f'] >= 100].iloc[0]['date']
                    turnover_days = df_db.query('cum_turnover <= 100').shape[0]
                    turnover_days_f = df_db.query('cum_turnover_f <= 100').shape[0]
                    bit = 1
                    #检查100%换手率的数据
                    #print(df_db.query('cum_turnover <= 100'))
                    print(f"{code}|{e_date}前数{n}日数据有效，对应换手日期{turnover_date}|{turnover_date_f}；交易日{turnover_days}|{turnover_days_f}")
                    #更新数据库
                    sql_update = text(f"update tspro_cumulative_turnover set turnover_date = '{turnover_date}' , turnover_date_f = '{turnover_date_f}' , turnover_days = {turnover_days} , turnover_days_f = {turnover_days_f} , turnover_valid = {bit} where code = '{code}' and date = '{e_date}'")
                    try:
                        with self.engine.begin() as connection:
                            connection.execute(sql_update)
                    except exc.ResourceClosedError:
                        print(f"更新{code}|{e_date}序列失败！")                    
                    #数据有效，跳出for循环
                    break
                else:
                    #累加值未超过100，数据无效
                    print(f"{code}前数{n}日数据无效，继续增加天数")
                    turnover_date = None
                    turnover_date_f = None
                    #这里还有一种情况，就是for列表循环完毕，数据依旧无效
                    if n == 5000:
                        print(f"未找到100%换手数据，可能数据无效也可能是新股、次新股")
                        bit = 0
                        sql_update = text(f"update tspro_cumulative_turnover set turnover_valid = {bit}  where code = '{code}' and date = '{e_date}'")
                        try:
                            with self.engine.begin() as connection:
                                connection.execute(sql_update)
                        except exc.ResourceClosedError:
                            print(f"更新{code}|{e_date}序列失败！")                             
                        #raise ValueError(f"{code}前数{n}日数据无效，程序终止")
    
if __name__=="__main__":
    tspro = data()
    tspro.code ='689009.sh'
    tspro.start_date= datetime(2023,4,3,8)
    tspro.end_date = datetime(2024,1,26,16)
    df = tspro.get_k_data()
    print(df)
    #ETF数据1998/10/19 含
    tspro.fq = tspro.复权.动态复权
    tspro.ktype = '1d'
    #tspro.update_cumulative_turnover()
    print(tspro.get_p_data())
    tspro.analyse_cumulative_turnover()
    
    tspro.update_day_ETF()
    tspro.update_factor_ETF()
