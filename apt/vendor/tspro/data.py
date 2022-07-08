import numpy as np
import pandas as pd
import tushare as ts
import sqlalchemy
import akshare as ak
from sqlalchemy import create_engine,exc   #用来捕捉sqlalchemy的异常
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

    def update_day(self):
        """
        tusharePro数据日常更新的主入口（按天更新）
        本模块只支持日线格式更新（日线数据按日进行全部数据的获取，因此与分时线的逻辑有所不同）
        更新逻辑：
            1. 获取需要更新的时间周期中的交易日
            2. 循环读取证券代码列表进行更新
                2.1 读取数据库中单个代码在两个日期间的数据
                2.2 没有数据则直接写入操作
                2.3 存在数据，则去重后写入
        """
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
            if count > 0 :
                #此处存在数据，不进入更新序列，直接跳过
                print(f"{day.strftime('%Y-%m-%d')}存在数据，跳过更新")
            else:
                #不存在数据，进行更新
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
                    print("%s 当日数据为空，跳过上传(该日为交易日，数据截取可能存在问题)" % (day.strftime('%Y%m%d')))
                else:
                    df.to_sql(
                            name = f'tspro_{self.ktype}',
                            con = self.engine,
                            index = False,
                            if_exists = 'append')
                    print(f"{day.strftime('%Y%m%d')}数据已上传完成({self.ktype})")
    
    def update_etf_day(self):
        #测试ETF复权因子
        #etf_factor = self.pro.fund_adj(trade_date = '20220701')
        #print(etf_factor)
        #测试ETF日线数据
        etf_day = self.pro.fund_daily(trade_date = '20220701')
        print(etf_day)
        #测试ETF分时线
        eft_min = ts.pro_bar(api = self.api , ts_code = '159949.SZ', freq = '60min' , adj = None , start_date = self.start_date.strftime('%Y%m%d') , end_date = (self.end_date + timedelta(days = 1)).strftime('%Y%m%d') , asset = 'FD')
        print(eft_min)
        #测试ETF列表
        pass
    def update_sequence_add(self , type = '60m'):
        '''
        task346更改了分时线数据更新的逻辑，拆分成add和launch两部分
        add模块主要进行数据更新任务的导入
        输入：
            type 更新类型 默认60m；目前可接受参数：60m/1m 未来可能还会继续添加
        '''
        #type数据校验
        if type not in ['1d','60m','1m']:
            raise ValueError(f'无效的数据类型')
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
            code_list = sec.get_all_code(day = self.end_date)
            code_list['start_date'] = self.start_date
            code_list['end_date'] = self.end_date
            code_list['type'] = type
            code_list = code_list[['code','start_date','end_date','type']]
            code_list.to_sql(
                    name = f'tspro_update_sequence',
                    con = self.engine,
                    index = False,
                    if_exists = 'append')
            print(f"上传已完成，新增{code_list.shape[0]}条更新序列！")

        elif result == '2':             #删除后添加
            sql_count = 'delete from tspro_update_sequence'
            try:    #删除需捕捉异常，否则会报错
                pd.read_sql_query(sql_count , self.engine)
            except exc.ResourceClosedError:
                pass
            #以下代码与选项1保持一致
            #1. 获取区间最后一天所对应的全部证券列表
            sec = security()
            code_list = sec.get_all_code(day = self.end_date)
            code_list['start_date'] = self.start_date
            code_list['end_date'] = self.end_date #add模块中日期不需要+1
            code_list['type'] = type
            code_list = code_list[['code','start_date','end_date','type']]
            code_list.to_sql(
                    name = f'tspro_update_sequence',
                    con = self.engine,
                    index = False,
                    if_exists = 'append')
            print(f"上传已完成，新增{code_list.shape[0]}条更新序列！")

        elif result == '3':             #直接删除
            sql_count = 'delete from tspro_update_sequence'
            try:    #删除需捕捉异常，否则会报错
                pd.read_sql_query(sql_count , self.engine)
            except exc.ResourceClosedError:
                print('更新序列已删除！')

        elif result == '4':          #不做任何更改，直接跳出
            return 
        else:
            raise ValueError(f'无效的输入')

    def update_sequence_launch(self):
        '''
        task346更改了分时线数据更新的逻辑，拆分成add和launch两部分
        launch模块主要进行数据更新任务，支持点断续传
        '''
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
                type = row['type']
                #tspro pro_bar数据获取模块（这里对最后日期做了day+1的处理）
                df_tspro = ts.pro_bar(api = self.api , ts_code = code, freq = self.dict[type] , adj = None , start_date = start_date.strftime('%Y%m%d') , end_date = (end_date + timedelta(days = 1)).strftime('%Y%m%d') , adjfactor = True , factors = ['tor', 'vr'] , asset = 'E')
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
                query_db = f"select code,date,open,close,high,low,volume,money from tspro_{type} where date(date) between '{start_date}' and '{end_date}' and code = '{code}'"
                df_db = pd.read_sql_query(query_db , self.engine)
                df_db['date'] = pd.to_datetime(df_db['date'])
                #print(df_tspro)
                #5. 两个DataFrame进行差值处理
                df_diff = pd.concat([df_tspro , df_db , df_db] ).drop_duplicates(subset=['date'] , keep = False)
                #print(df_diff)
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
                sql_delete = f'delete from tspro_update_sequence where id = {id}'
                try:    #删除需捕捉异常，否则会报错
                    pd.read_sql_query(sql_delete , self.engine)
                except exc.ResourceClosedError:
                    pass
                    #print('更新序列已删除！')
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
        trade_days = self.pro.trade_cal(exchange = 'SSE', start_date = self.start_date.strftime('%Y%m%d'), end_date=self.end_date.strftime('%Y%m%d'))
        #剔除非交易日
        trade_days.query('is_open == 1' , inplace = True)
        trade_days['cal_date'] = pd.to_datetime(trade_days['cal_date'])
        #3. 获取tspro相应的数据
        for code in code_list['code']:
            #目前量比 vor 复权因子均无效 
            #tspro pro_bar数据获取模块（这里对最后日期做了day+1的处理）
            df_tspro = ts.pro_bar(api = self.api , ts_code = code, freq = self.dict[self.ktype] , adj = None , start_date = self.start_date.strftime('%Y%m%d') , end_date = (self.end_date + timedelta(days = 1)).strftime('%Y%m%d') , adjfactor = True , factors = ['tor', 'vr'] , asset = 'E')
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

    def update_factor(self):
        """
        tusharePro复权因子日常更新的主入口（按天更新）
        更新逻辑：
            1. 获取需要更新的时间周期中的交易日
            2. 循环读取证券代码列表进行更新
                2.1 读取数据库中单个代码在两个日期间的数据
                2.2 没有数据则直接写入操作
                2.3 存在数据，则去重后写入
        """
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
            if count > 0 :
                #此处存在数据，不进入更新序列，直接跳过
                print(f"{day.strftime('%Y-%m-%d')}存在数据，跳过更新")
            else:
                #不存在数据，进行更新
                df = self.pro.query('adj_factor',  trade_date = day.strftime('%Y%m%d'))
                #print(df)
                #df = self.pro.daily(trade_date= day.strftime('%Y%m%d'))
                #根据wiki描述的数据库一致性的要求，进行列名的变更 https://huiqiao.visualstudio.com/MyFunds/_wiki/wikis/MyFunds.wiki/19/tusharePro%E6%95%B0%E6%8D%AE%E8%AF%8D%E5%85%B8
                #df.rename(columns={'ts_code': 'code', 'trade_date': 'date' , 'vol': 'volume' , 'amount': 'money'} , errors="raise")
                #df.rename(columns={"ts_code": "code", "trade_date": "date" } , errors="raise")
                df.rename(columns={"ts_code": "code", "trade_date": "date" ,"adj_factor" : "factor" } , errors="raise" , inplace = True)           
                #时间日期类的列进行类型变更
                df['date'] = pd.to_datetime(df['date'])
                #保存至数据库
                if df.empty == True:
                    print("%s 当日数据为空，跳过上传(该日为交易日，数据截取可能存在问题)" % (day.strftime('%Y%m%d')))
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
        flag_resample：T/F 用于标识是否进行重采样
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

if __name__=="__main__":
    tspro = data()
    tspro.code ='601318.sh'
    tspro.start_date= datetime(2022,7,5,8)
    tspro.end_date = datetime(2022,7,7,16)
    tspro.fq = tspro.复权.动态复权
    tspro.ktype = '1d'
    tspro.update_factor_ETF()
