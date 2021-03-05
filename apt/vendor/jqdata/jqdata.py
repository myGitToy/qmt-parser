import numpy as np
import pandas as pd
import tushare as ts
import sqlalchemy
import datetime
from jqdatasdk import *
from apt.vendor.jqdata.base import base as base


class data(base):
    def update_v1(self , code_list = None , start_date = datetime.datetime(2020,1,1,1) , end_date = datetime.datetime.now() , ktype = '5m' ):
        """
        聚宽数据日常更新的主入口 第一版本 使用双循环策略，判断简单但数据库操作偏多，每天每代码都要执行一遍读取、判断、写入
        适用场景：
            1. 对时间要求不高的高准确性更新场景
            2. 对更新工作进行校验的场景，比如检查每月是否有遗漏日期（即V2V3更新后，再用V1重新跑一彼遍进行校验）
        不适用场景：
            1. 日内更新（当天有数据则会跳过，因此不适用日内反复更新最新数据的场景）
        适合进行1m 5m数据更新
        code_list 需要更新的代码列表，默认为空，即全部更新
        start_date 开始时间，默认为2020年
        end_date 结束时间 默认为当前时间（更新函数中默认不更新当天的及时数据，因为会造成重复录入，请注意）
        ktype K线周期 1d 5m 60m等
        更新逻辑：
            1. 获取需要更新的时间周期中的交易日
            2. 循环读取证券代码列表进行更新
                2.1 读取数据库中单个代码在两个日期间的数据
                2.2 没有数据则直接写入操作
                2.3 存在数据，则去重后写入
        """
        #更新时段校验 如果更新的是日线数据且校验为更新时段，则不予以更新
        check = self.get_today_is_trade()
        if check == self.交易时段校验.交易时段:
            print("update_V1规则不允许在交易时段进行更新")
            return 0
        #获取交易日期
        trade_days = get_trade_days(start_date = start_date , end_date = end_date)
        #获取更新列表
        if code_list == None:
            #更新列表未填写，则默认为空，即全部更新
            code_list = list(get_all_securities(['stock','etf'],date = end_date).index)
        #设置规则下需要更新的数目（按一天的量进行计算）
        update_num = self.__get_update_count(trade_days = 1 , ktype = ktype)
        for day in trade_days:
            print("##############正在更新%s数据##############" % day.strftime("%Y-%m-%d"))
            df_remain = get_query_count()
            print("当日数据剩余条目数：%s" % df_remain)
            #print(datetime.now())
            for code in code_list:
                #检查数据库是否存在数据
                query = "select count(code) as num from jqdata_%s where code = '%s' and date(date) = '%s'" % (ktype , code , day)
                df_old = pd.read_sql_query(query , self.engine)
                count = df_old.loc[0 , 'num']
                if count > 0 :
                    #此处存在数据，不进入更新序列，直接跳过
                    print("%s存在数据，跳过更新" % code)
                else:
                    #不存在数据，进行更新
                    #此处使用该方法进行日期重定位的原因：
                        #1. day的数据格式为datetime.date，无法进行+timedelta(hours=16)这样的操作
                        #2. 如果仅输入day参数，则时间默认为当天零点，所以实际更新的是前一天的数据
                    end_day = datetime.datetime(day.year,day.month,day.day,16)
                    #print(end_day)
                    if  ktype == '1d':
                        #1. 日线数据需要进行偏移处理
                        #2. 筛选作业
                        dday = day + datetime.timedelta(days=1)
                        df = get_bars(security = code , count = update_num , unit = ktype , fields = ['date', 'open', 'close', 'high', 'low', 'volume', 'money','factor'] , include_now = False , end_dt = dday , df = True)
                        df['code']= code
                        #日线数据特殊处理，因为数据库中的格式是date，不是datetime
                        df = df[(df.date == day)]
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
                        print("%s 当日数据为空，跳过上传" % (code))
                    else:
                        df.to_sql(
                                name = 'jqdata_%s' % (ktype),
                                con = self.engine,
                                index = False,
                                if_exists = 'append')
                        print("%s 数据已上传完成(%s)" % (code,ktype))

    def update_v2(self , code_list = None , start_date = datetime.datetime(2020,1,1,1) , end_date = datetime.datetime.now() , ktype = '1d' ):
        """
        聚宽数据日常更新的主入口 第二版本 使用单循环策略，所有更新只循环4000次
        code_list 需要更新的代码列表，默认为空，即全部更新
        start_date 开始时间，默认为2020年
        end_date 结束时间 默认为当前时间（交易日盘中更新日线数据会直接否决）
        ktype K线周期 1d 5m 60m等 默认1d日线数据
        更新逻辑：
            1. 获取需要更新的时间周期中的交易日
            2. 循环读取证券代码列表进行更新
                2.1 读取数据库中单个代码在两个日期间的数据
                2.2 没有数据则直接写入操作
                2.3 存在数据，则去重后写入
        适用场景或优点：
            1. 开始和结束日期间的数据量有校验功能，有停牌等不符合的情况会全部重新下载数据并同数据库进行对比去重后进行写入 
        不适用场景或缺点：
            1. 因为适用场景1的逻辑，对更新条目数的消耗量会比较大
            2. 由于更新周期不同，比如场内基金20:00以后才会出数据，比如12.18日晚18:00更新了全部数据，
                并将最后更新日期重置到12.19，这样的话其实场内基金再12.18日的数据是没有获取成功的
        """
        #更新时段校验 如果更新的是日线数据且校验为更新时段，则不予以更新
        check = self.get_today_is_trade()
        if (ktype == '1d') and (check == self.交易时段校验.交易时段):
            print("日线数据不允许在交易时段更新")
            return 0
        #获取交易日期
        trade_days = get_trade_days(start_date = start_date , end_date = end_date)
        #获取更新列表
        if code_list == None:
            #更新列表未填写，则默认为空，即全部更新
            code_list = list(get_all_securities(['stock','etf'],date = end_date).index)
        for code in code_list:
            #检查数据库是否存在数据
            query = "select count(code) as num from jqdata_%s where code = '%s' and date(date) BETWEEN '%s' and '%s'" % (ktype , code , start_date.strftime("%Y-%m-%d") , end_date.strftime("%Y-%m-%d"))
            df_old = pd.read_sql_query(query , self.engine)
            #获取数据库实际存在的数据
            count_db = df_old.loc[0 , 'num']
            #获取数据里理论上应该存在的数据
            count_suppose = self.__get_update_count(trade_days = len(trade_days) , ktype = ktype)
            if count_db == count_suppose :
                #数据库中存在数据且数据条目等于理论条目数，不进入更新序列，直接跳过
                print("%s存在数据，且校验通过，跳过更新" % code)
            elif count_db <= count_suppose :
                #数据库中数据条目小于理论条目数  无论数据库数据是否为零，获取新数据后予以合并，写入数据库库
                #此处使用该方法进行日期重定位的原因(新版本这里已经不再需要了，参数中直接输入含16点的日期)：
                    #1. day的数据格式为datetime.date，无法进行+timedelta(hours=16)这样的操作
                    #2. 如果仅输入day参数，则时间默认为当天零点，所以实际更新的是前一天的数据
                #end_day = datetime.datetime(day.year,day.month,day.day,16)
                #print(end_day)
                #日线进行日期偏移，需要特殊处理
                if ktype == '1d': 
                    end_date = end_date + datetime.timedelta(days=1)
                df_jqdata = get_bars(security = code , count = count_suppose , unit = ktype , fields = ['date', 'open', 'close', 'high', 'low', 'volume', 'money','factor'] , include_now = False , end_dt = end_date , df = True)
                df_jqdata['code'] = code
                #df_jqdata.to_csv('.\\data\\399001_jqdata.csv', encoding = 'utf_8_sig')
                #print(df_jqdata)
                #数据去重（因为停盘的关系，比如获取1/1-1/30号的数据，实际通过count取到的数据可能包含前面12月份的，直接写入因为唯一索引的约束，会报错）
                if  ktype == '1d':
                    #日线数据特殊处理，因为数据库中的格式是date，不是datetime
                    df_jqdata = df_jqdata[(df_jqdata.date >= start_date.date()) & (df_jqdata.date <= end_date.date())]
                    #print(df_jqdata)
                else:
                    #分时数据正常处理
                    df_jqdata = df_jqdata[(df_jqdata.date >= start_date) & (df_jqdata.date <= end_date)]
                #数据去除NA（在极特殊的情况下会引发异常 数据库字段NOT NULL 冲突）
                df_jqdata.dropna(inplace = True)
                #检索数据库中的数据
                query2 = "select date from jqdata_%s where code = '%s' and date(date) BETWEEN '%s' and '%s'" % (ktype , code , start_date.strftime("%Y-%m-%d") , end_date.strftime("%Y-%m-%d"))         
                df_db = pd.read_sql_query(query2 , self.engine)
                #将新老库合并，求差集
                df_jqdata = df_jqdata.append(df_db)
                df_jqdata.drop_duplicates(subset = ['date'] , keep = False ,inplace = True)
                #print(df_jqdata)
                #保存至数据库
                if df_jqdata.empty == True:
                    print("%s 进行差集处理后剩余数据为空或者jqdata无数据，跳过上传" % (code))
                else:
                    df_jqdata.to_sql(
                            name = 'jqdata_%s' % (ktype),
                            con = self.engine,
                            index = False,
                            if_exists = 'append')
                    print("%s 数据已上传完成(%s)" % (code,ktype))  

    def update_v3(self , code_list = None , start_date = datetime.datetime(2020,1,1,1) , end_date = datetime.datetime.now() , ktype = '1d' ):
        """
        聚宽数据日常更新的主入口 第三版本 使用单循环策略，所有更新只循环4000次
        code_list 需要更新的代码列表，默认为空，即全部更新
        start_date 开始时间，默认为2020年
        end_date 结束时间 默认为当前时间（更新函数中默认不更新当天的即时数据，因为会造成重复录入，请注意）
        ktype K线周期 1d 5m 60m等
        更新逻辑：
            1. 获取需要更新的时间周期中的交易日
            2. 循环读取证券代码列表进行更新
                2.1 读取数据库中单个代码在两个日期间的数据
                2.2 没有数据则直接写入操作
                2.3 存在数据，则去重后写入
        """
        #更新时段校验 如果更新的是日线数据且校验为更新时段，则不予以更新
        check = self.get_today_is_trade()
        if (ktype == '1d') and (check == self.交易时段校验.交易时段):
            print("日线数据不允许在交易时段更新")
            return 0
        #获取交易日期
        trade_days = get_trade_days(start_date = start_date , end_date = end_date)
        #获取更新列表
        if code_list == None:
            #更新列表未填写，则默认为空，即全部更新
            code_list = list(get_all_securities(['stock','etf'],date = end_date).index)
        for code in code_list:
            #检查数据库是否存在数据
            query = "select count(code) as num from jqdata_%s where code = '%s' and date(date) BETWEEN '%s' and '%s'" % (ktype , code , start_date.strftime("%Y-%m-%d") , end_date.strftime("%Y-%m-%d"))
            df_old = pd.read_sql_query(query , self.engine)
            #获取数据库实际存在的数据
            count_db = df_old.loc[0 , 'num']
            #获取数据里理论上应该存在的数据
            count_suppose = self.__get_update_count(trade_days = len(trade_days) , ktype = ktype)
            if count_db == count_suppose :
                #数据库中存在数据且数据条目等于理论条目数，不进入更新序列，直接跳过
                print("%s存在数据，且校验通过，跳过更新" % code)
            elif count_db <= count_suppose :
                #数据库中数据条目小于理论条目数  无论数据库数据是否为零，获取新数据后予以合并，写入数据库库
                #此处使用该方法进行日期重定位的原因(新版本这里已经不再需要了，参数中直接输入含16点的日期)：
                    #1. day的数据格式为datetime.date，无法进行+timedelta(hours=16)这样的操作
                    #2. 如果仅输入day参数，则时间默认为当天零点，所以实际更新的是前一天的数据
                #end_day = datetime.datetime(day.year,day.month,day.day,16)
                #print(end_day)
                #日线进行日期偏移，需要特殊处理
                if ktype == '1d': 
                    end_date = end_date + datetime.timedelta(days=1)
                df_jqdata = get_bars(security = code , count = count_suppose , unit = ktype , fields = ['date', 'open', 'close', 'high', 'low', 'volume', 'money','factor'] , include_now = False , end_dt = end_date , df = True)
                df_jqdata['code'] = code
                #print(df_jqdata)
                #数据去重（因为停盘的关系，比如获取1/1-1/30号的数据，实际通过count取到的数据可能包含前面12月份的，直接写入因为唯一索引的约束，会报错）
                if  ktype == '1d':
                    #日线数据特殊处理，因为数据库中的格式是date，不是datetime
                    df_jqdata = df_jqdata[(df_jqdata.date >= start_date.date()) & (df_jqdata.date <= end_date.date())]
                    #print(df_jqdata)
                else:
                    #分时数据正常处理
                    df_jqdata = df_jqdata[(df_jqdata.date >= start_date) & (df_jqdata.date <= end_date)]
                #数据去除NA（在极特殊的情况下会引发异常 数据库字段NOT NULL 冲突）
                df_jqdata.dropna(inplace = True)
                #检索数据库中的数据
                query2 = "select date from jqdata_%s where code = '%s' and date(date) BETWEEN '%s' and '%s'" % (ktype , code , start_date.strftime("%Y-%m-%d") , end_date.strftime("%Y-%m-%d"))         
                df_db = pd.read_sql_query(query2 , self.engine)
                #将新老库合并，求差集
                df_jqdata = df_jqdata.append(df_db)
                df_jqdata.drop_duplicates(subset = ['date'] , keep = False ,inplace = True)
                #print(df_jqdata)
                #保存至数据库
                if df_jqdata.empty == True:
                    print("%s 进行差集处理后剩余数据为空或者jqdata无数据，跳过上传" % (code))
                else:
                    df_jqdata.to_sql(
                            name = 'jqdata_%s' % (ktype),
                            con = self.engine,
                            index = False,
                            if_exists = 'append')
                    print("%s 数据已上传完成(%s)" % (code,ktype))

    def check_validation(self , code_list = None , start_date = datetime.datetime(2020,1,1,1) , end_date = datetime.datetime.now()):
        """
        通过对比日线数据，检查分时线或者tick数据是否有缺失
        
        """
        ###1. 检查日线完整性

        ###2. 检查分时线数据完整性


        ###3. 检查tick数据完整性

        ###4. 检查分时线数据完整性
        pass

    def update_index(self , start_date = datetime.datetime(2020,1,1,1) , end_date = datetime.datetime.now() , ktype = '1d' ):
        """
        jqdata指数更新模块
        start_date 开始时间，默认为2020年
        end_date 结束时间 默认为当前时间（交易日盘中更新日线数据会直接否决）
        ktype K线周期 1d 5m 60m等 默认1d日线数据

        注：逻辑上调用update_v2，通过提供code_list的方式区分普通股票和指数更新（普通股票不需要提供code_list，指数需要）

        目前指数支持：
        000001.XSHG	上证指数
        000016.XSHG	上证50
        000010.XSHG	上证180
        000300.XSHG	沪深300
        000688.XSHG	科创50
        000905.XSHG	中证500
        000852.XSHG	中证1000指数
        399001.XSHE	深证成指
        399005.XSHE	中小板指
        399006.XSHE	创业板指
        """
        #全指数列表 目前暂不启用
        code_list = list(get_all_securities(['index'] , date = end_date).index)
        #优先更新指数列表
        #备注：399001.XSHG深成指在2019年11月的数据有错误
        code_list = ['000001.XSHG','000016.XSHG','000010.XSHG','000300.XSHG','000688.XSHG','000905.XSHG','000852.XSHG','399005.XSHE','399006.XSHE']
            
        #code_list = ['399001.XSHE']
        self.update_v2(code_list = code_list , start_date = start_date , end_date = end_date, ktype = ktype)

    def get_k_data(self , code = None ,  
                 start_date = datetime.datetime(2020,1,1,1,8) , end_date = datetime.datetime.now()  , 
                 col = ['code','date','open','close','high','low','volume','money','factor'] , 
                 ktype = '1d' , fq = base.复权.动态复权):
        
        """
        jqdata数据加载模块
        start_time：开始时间 最好带上小时参数  比如(2020,12,31,8)
        end_time：结束时间 最好带上小时参数  比如(2020,12,31,16)
        接受前复权 后复权 不复权 动态复权四种复权模式
        成交量、成交额目前未进行复权处理
        """
        query = "select * from jqdata_%s where code = '%s' and date BETWEEN '%s' and '%s' order by date asc" % (ktype , code , start_date, end_date)         
        df_db = pd.read_sql_query(query , self.engine)
        if df_db.empty == True:
            #无数据
            print("无数据")
            return pd.dataframe()
        else:
            #有数据，进行复权处理
            if fq == self.复权.不复权:
                return df_db
            elif fq ==self.复权.前复权:
                #前复权价格 = 当日价格 / 最后一个交易日（非end_date）的复权因子 * 当日复权因子
                factor = self.__get_last_factor(code = code)
                df_db['open'] = df_db['open'] / factor * df_db['factor']
                df_db['high'] = df_db['high'] / factor * df_db['factor']
                df_db['low'] = df_db['low'] / factor * df_db['factor']
                df_db['close'] = df_db['close'] / factor * df_db['factor']
                return df_db[col]
            elif fq ==self.复权.后复权:
                #后复权价格 = 当日价格 / 第一个交易日（start_date）的复权因子 * 当日复权因子    
                #获取第一一个复权因子的数值
                factor = df_db.iloc[0].at['factor']
                df_db['open'] = df_db['open'] / factor * df_db['factor']
                df_db['high'] = df_db['high'] / factor * df_db['factor']
                df_db['low'] = df_db['low'] / factor * df_db['factor']
                df_db['close'] = df_db['close'] / factor * df_db['factor']
                return df_db[col]
            elif fq ==self.复权.动态复权:
                #动态复权价格 = 当日价格 / 区间最后一天的复权因子 * 当日复权因子
                #获取最后一个复权因子的数值
                factor = df_db.iloc[-1].at['factor']
                df_db['open'] = df_db['open'] / factor * df_db['factor']
                df_db['high'] = df_db['high'] / factor * df_db['factor']
                df_db['low'] = df_db['low'] / factor * df_db['factor']
                df_db['close'] = df_db['close'] / factor * df_db['factor']
                return df_db[col]
            else:
                print("不支持的复权模式，请检查！")
                return df_db

    def jqdata_to_backtrader(self , df = None):
        """
        将jqdata数据格式转换成backtrader格式
        """
        if df.empty == True:
            #无数据
            print("无有效数据 请检查")
            return pd.dataframe()
        else:
            #有数据
            df['openinterest'] = 0
            df['datatime'] = pd.to_datetime(df['date'])
            df.set_index(['datatime'], inplace=True)
            return df[['open','high','low','close','volume','openinterest']]
    def __get_last_factor(self , code = None , day = datetime.datetime(2020,12,1)):
        """
        获取指定股票的最后复权因子（内部函数）
        """
        query = "select date,factor from jqdata_1d where code = '%s' and date >= '%s' order by date desc limit 1" % ( code , day.strftime("%Y-%m-%d"))         
        df_db = pd.read_sql_query(query , self.engine)
        return df_db.iloc[0].at['factor']

    def __get_update_count (self , trade_days = None , ktype = '1d'):
        """
        获取需要更新的条目数（内部函数）
        trade_days 期间交易日
        ktype K线周期 1d 5m 60m等
        返回：根据ktype和交易日计算出来的K线数据
        """
        if trade_days == None:
            print("交易日间隔天数设置错误，请检查")
            return 0
        if ktype == '1d':
            return trade_days * 1
        elif ktype in ('5m','15m','30m','60m','120m'):
            return int(240 / int(ktype.replace('m','')) * trade_days)
        else:
            print("输入错误，请检查")
            return 0

    def get_today_is_trade(self ):
        """
        获取今天是否是交易日和交易时段
        用于更新日线数据时判断是否能够进行更新操作
        更新逻辑中对于日线数据有一条规则：交易日盘中不得进行日线数据更新
        """
        #today = datetime.datetime(2020,12,16,12)
        today = datetime.datetime.now()
        check_valid = get_trade_days(end_date = today, count = 1)
        if check_valid == today.date():
            #属于交易日
            if  datetime.time(9,0,0) < today.time() < datetime.time(15,30,0):
                #交易时段
                return self.交易时段校验.交易时段
            else:
                return self.交易时段校验.非交易时段
        else:
            #不属于交易日
            return self.交易时段校验.非交易日
