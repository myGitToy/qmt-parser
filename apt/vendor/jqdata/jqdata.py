import numpy as np
import pandas as pd
import tushare as ts
import sqlalchemy
import datetime
from jqdatasdk import *
from apt.vendor.jqdata.base import base as base


class data(base):
    def update_byday(self , code_list = None , start_date = datetime.datetime(2020,1,1,1) , end_date = datetime.datetime.now() , ktype = '5m' ):
        """
        聚宽数据日常更新的主入口 第一版本 使用双循环策略，判断简单但数据库操作偏多，每天每代码都要执行一遍读取、判断、写入
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
        print("更新主入口")
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
                query = "select count(code) as num from jqdata_%s where code = '%s' and left(date,10) = '%s'" % (ktype , code , day)
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
                    df = get_bars(security = code , count = update_num , unit = ktype , fields = ['date', 'open', 'close', 'high', 'low', 'volume', 'money','factor'] , include_now = False , end_dt = end_day , df = True)
                    df['code']= code
                    #进行当天数据的筛选，因为比如取5m数据，当天有48根，但可能上午停牌，因此48根数据就包含了昨天下午的，此时写入数据库会造成唯一索引约束错误
                    df = df[(df.date >= datetime.datetime(day.year,day.month,day.day,1))& (df.date <= datetime.datetime(day.year,day.month,day.day,16))]
                    #print(df)
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

    def update(self , code_list = None , start_date = datetime.datetime(2020,1,1,1) , end_date = datetime.datetime.now() , ktype = '1d' ):
        """
        聚宽数据日常更新的主入口 第二版本 使用单循环策略，所有更新只循环4000次
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
        #获取交易日期
        trade_days = get_trade_days(start_date = start_date , end_date = end_date)
        #获取更新列表
        if code_list == None:
            #更新列表未填写，则默认为空，即全部更新
            code_list = list(get_all_securities(['stock','etf'],date = end_date).index)
        for code in code_list:
            #检查数据库是否存在数据
            query = "select count(code) as num from jqdata_%s where code = '%s' and left(date,10) BETWEEN '%s' and '%s'" % (ktype , code , start_date.strftime("%Y-%m-%d") , end_date.strftime("%Y-%m-%d"))
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
                query2 = "select date from jqdata_%s where code = '%s' and left(date,10) BETWEEN '%s' and '%s'" % (ktype , code , start_date.strftime("%Y-%m-%d") , end_date.strftime("%Y-%m-%d"))         
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