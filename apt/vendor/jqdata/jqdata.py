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
            raise ValueError(f'update_V1规则不允许在交易时段进行更新')
        #获取交易日期
        trade_days = get_trade_days(start_date = start_date , end_date = end_date)
        #获取更新列表
        if code_list == None:
            #更新列表未填写，则默认为空，即全部更新
            code_list = list(get_all_securities(['stock','etf'],date = end_date).index)
        #设置规则下需要更新的数目（按一天的量进行计算）
        update_num = self.__get_update_count(trade_days = 1 , ktype = ktype)
        for day in trade_days:
            print(f"##############正在更新%s数据##############" % day.strftime("%Y-%m-%d"))
            df_remain = get_query_count()
            #print("当日数据剩余条目数：%s" % df_remain)
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
            #新版逻辑可以在盘中更新T-1日前的日线数据
            #盘中更新日线数据再加一层判断：是否更新当日的数据
            day_T = datetime.datetime.now()
            if end_date.date() == day_T.date():
                end_date = datetime.datetime.now()+datetime.timedelta(days=-1)
                print("日线数据盘中仅更新至T-1日")

            #print("日线数据不允许在交易时段更新")
            #return 0
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
                    end_date = end_date + datetime.timedelta(days = 1)
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
                    try:
                        df_jqdata.to_sql(
                                name = 'jqdata_%s' % (ktype),
                                con = self.engine,
                                index = False,
                                if_exists = 'append')
                        print("%s 数据已上传完成(%s)" % (code,ktype))  
                    except:
                        print(f"{code} {ktype}更新错误，跳过")

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
            raise ValueError(f'日线数据不允许在交易时段更新')
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

    def re_update(self , code = None , start_date = datetime.datetime(2020,1,1,1) , end_date = datetime.datetime.now() , ktype_list =['1d','5m','30m','60m'] ):
        """
        对指定代码进行数据重新更新
        函数说明：
            1. 某些数据出现错误，需要对区间数据进行重置
            2. 删除区间内的数据
            3. 重新从jqdata中拉取数据，并写入数据库
        输入：
        code 需要更新的代码列表，默认为空，即全部更新
        start_date 开始时间，默认为2020年
        end_date 结束时间 默认为当前时间（更新函数中默认不更新当天的及时数据，因为会造成重复录入，请注意）
        ktype_list 需要更新数据的ktype列表 默认['1d','5m','30m','60m']
        更新逻辑：
            1. 获取需要更新的时间周期中的交易日
            2. 循环读取证券代码列表进行更新
                2.1 读取数据库中单个代码在两个日期间的数据
                2.2 没有数据则直接写入操作
                2.3 存在数据，则去重后写入
        """
        for type in ktype_list:
            ####1. 删除数据库相关
            sql_delete =f"delete from jqdata_{type} where code = '{code}' and date(date) between '{start_date}' and '{end_date}'"
            try:
                tt = pd.read_sql_query(sql_delete , self.engine)
            except:
                pass
            ####2. 更新数据
            print(f'更新{code}|{type}数据')
            lst = []
            lst.append(code)
            self.update_v2(code_list = lst , start_date = start_date , end_date = end_date , ktype = type)
            
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
        #code_list = list(get_all_securities(['index'] , date = end_date).index)
        #优先更新指数列表
        #备注：399001.XSHG深成指在2019年11月的数据有错误
        #code_list =['399001.XSHE']
        code_list = ['000001.XSHG','000016.XSHG','000010.XSHG','000300.XSHG','000688.XSHG','000905.XSHG','000852.XSHG','399001.XSHE','399005.XSHE','399006.XSHE']
            
        #code_list = ['399001.XSHE']
        self.update_v2(code_list = code_list , start_date = start_date , end_date = end_date, ktype = ktype)

    def get_k_data(self , code = None , start_date = datetime.datetime(2005,1,1,1,8) ,end_date = datetime.datetime.now()  , 
                 count = None ,
                 col = ['code','date','open','close','high','low','volume','money','factor'] , 
                 ktype = '1d' , 
                 fq = base.复权.动态复权):
        
        """
        jqdata数据加载模块
        start_time：开始时间 最好带上小时参数  比如(2020,12,31,8)
        end_time：结束时间 最好带上小时参数  比如(2020,12,31,16)
        count : 获取K线条目的个数 默认是全部输出  
        接受前复权 后复权 不复权 动态复权四种复权模式
        成交量、成交额目前未进行复权处理
        返回的数据按照升序排列（backtrader要求的数据格式）
        """
        if start_date  > end_date:
            raise ValueError(f'开始日期必须早于结束日期')
        if ktype not in ['1d','1m','5m','30m','60m']:
            raise ValueError(f'不合规的K线类型: {ktype}')
        if code == None :
            raise ValueError(f'证券代码不能为空')
        query = f"select * from jqdata_{ktype} where code = '{code}' and date BETWEEN '{start_date}' and '{end_date}' order by date asc"         
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
            #有数据，进行复权处理
            if fq == self.复权.不复权:
                return df_db.iloc[-count:][col]
            elif fq ==self.复权.前复权:
                #前复权价格 = 当日价格 / 最后一个交易日（非end_date）的复权因子 * 当日复权因子
                factor = self.__get_last_factor(code = code)
                df_db['open'] = df_db['open'] / factor * df_db['factor']
                df_db['high'] = df_db['high'] / factor * df_db['factor']
                df_db['low'] = df_db['low'] / factor * df_db['factor']
                df_db['close'] = df_db['close'] / factor * df_db['factor']
                return df_db.iloc[-count:][col]
            elif fq ==self.复权.后复权:
                #后复权价格 = 当日价格 / 第一个交易日（start_date）的复权因子 * 当日复权因子    
                #获取第一一个复权因子的数值
                factor = df_db.iloc[0].at['factor']
                df_db['open'] = df_db['open'] / factor * df_db['factor']
                df_db['high'] = df_db['high'] / factor * df_db['factor']
                df_db['low'] = df_db['low'] / factor * df_db['factor']
                df_db['close'] = df_db['close'] / factor * df_db['factor']
                return df_db.iloc[-count:][col]
            elif fq ==self.复权.动态复权:
                #动态复权价格 = 当日价格 / 区间最后一天的复权因子 * 当日复权因子
                #获取最后一个复权因子的数值
                factor = df_db.iloc[-1].at['factor']
                df_db['open'] = df_db['open'] / factor * df_db['factor']
                df_db['high'] = df_db['high'] / factor * df_db['factor']
                df_db['low'] = df_db['low'] / factor * df_db['factor']
                df_db['close'] = df_db['close'] / factor * df_db['factor']
                return df_db.iloc[-count:][col]
            else:
                raise ValueError(f'不支持的复权模式，请检查！')
                return df_db
    def get_close_range(self , code = None , start_date = datetime.datetime(2005,1,1,1,8) , end_date = datetime.datetime.now() , ktype = '1d' , fq = base.复权.动态复权  , start_offset = 0 , end_offset = 0):     
        """
        获取指定代码在日期区间的收盘价
        start_time：开始时间比如(2020,12,31)
        end_time：结束时间比如(2020,12,31
        接受前复权 后复权 不复权 动态复权四种复权模式
        成交量、成交额目前未进行复权处理
        start_offset：起始日期的offset值，默认为0；因为backtrader从开始日期取数后，要全部数据准备齐全才能提供回测
        end_offset：结束日期的offset值，默认为0；目前暂无实装
        返回：
            dict : {'beginning_close , ending_close'} 期初收盘价 期末收盘价
        """
        df = self.get_k_data(code = code , start_date = start_date , end_date = end_date , ktype = ktype , fq = fq)
        return {'beginning_close': df.iloc[0].at['close'] , 'ending_close': df.iloc[-1].at['close'] , 'beginning_offset_close': df.iloc[0 + start_offset].at['close'] , 'ending_offset_close': df.iloc[- (1 + end_offset)].at['close']}

    def jqdata_to_backtrader(self , df = None):
        """
        将jqdata数据格式转换成backtrader格式
        """
        if df.empty == True:
            #无数据
            print("无有效数据 请检查")
            return pd.DataFrame()
        else:
            #有数据
            df['openinterest'] = 0
            df['datetime'] = pd.to_datetime(df['date'])
            df.set_index(['datetime'], inplace=True)
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
            raise ValueError(f'交易日间隔天数设置错误，请检查')
        if ktype == '1d':
            return trade_days * 1
        elif ktype in ('5m','15m','30m','60m','120m'):
            return int(240 / int(ktype.replace('m','')) * trade_days)
        else:
            raise ValueError(f'输入错误，请检查')

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
            if  datetime.time(9,0,0) < today.time() < datetime.time(15,15,0):
                #交易时段
                return self.交易时段校验.交易时段
            else:
                return self.交易时段校验.非交易时段
        else:
            #不属于交易日
            return self.交易时段校验.非交易日

    def read_excel(file_name = None , sheet_name = None):
        """
        读取excel数据
        注意事项：
            1. 默认引擎为xlrd，目前高版本已不支持xlsx文件
            2. 切换引擎至openpyxl 
            3. 上述两个引擎都需要额外pip install
            4. 表的名称和列的名称目前都支持中文
            5. 读取时excel表格必须处于关闭状态，否则会报错（已通过增加exception做到提示错误信息）
        """
        try:
            df = pd.read_excel( file_name, sheet_name = sheet_name , engine = 'openpyxl' )
            return df
        except Exception as e:
            print(str(e))
            return pd.DataFrame()

    def update_trader_days(self):
        """
        更新交易日数据，无需参数输入
        更新逻辑：
        1. 查询数据库中的最后更新日期
        2. 在此基础上+1 ，得到中间的交易天数
        3. 数据写入数据库
        交易日历提供自2005年起的数据
        """
        #获取数据库中存在的数据最后更新日期
        query2 = f"select date FROM jqdata_trader_days ORDER BY date DESC LIMIT 1" 
        df_db = pd.read_sql_query(query2 , self.engine)
        if df_db.empty == True:
            #数据库不存在数据
            new_start_date = datetime.datetime(2005,1,1)
        else:
            #数据库存在数据，新定义开始日期（数据库最后一天+1）
            new_start_date =  df_db.loc[0 , 'date']  + datetime.timedelta(days=1)   
        #获取修正后的日期间隔里的交易日期
        day_list = get_trade_days(start_date = new_start_date , end_date = datetime.datetime.now().date())
        #对数据进行处理，转换为DataFrame及重命名列
        trader_day = pd.DataFrame(day_list)
        trader_day.columns = ['date']    
        #保存至数据库 
        if trader_day.empty == True:
            print("交易日历已是最新版本，跳过更新")
        else:
            trader_day.to_sql(
                    name = 'jqdata_trader_days',
                    con = self.engine,
                    index = False,
                    if_exists = 'append')
            print("数据已上传完成[交易日历])")

    def get_trader_days(self , start_date = datetime.datetime(2000,1,1) ,end_date = datetime.datetime.now()):
        """
        获取指定范围内的交易日数据
        【输入】
        start_time：开始日期 最好带上小时参数
        end_time：结束日期 最好带上小时参数     【备注】这里未考虑是否存在最后日的问题，比如2021/11/29 系统实际是取到截至前一天的数据   
        【返回】
        DataFrame/
        """
        pass




    def get_all_code(self , end_date = datetime.datetime.now() , type = "'stock','etf'", local = True , min_cap = 0 , max_cap = 10000):
        """
        读取所有证券代码列表
        本函数提供下游K线形态、量价分析使用
        【输入】
            end_date 取代码的基准日期 默认为当天
            local 是否脱机查询 默认为脱机
            type 数据类型 "'stock','index','fund','etf','lof','fja','fjb'" 默认为stock+etf
            include_ETF 包含ETF数据 默认为否
            min_cap 最小市值(总市值)要求(单位：亿) 100亿则输入 默认为0
            max_cap 最大市值(总市值)要求(单位：亿) 10000万亿则输入 默认为10000亿
            min_daily_money_etf 最小交易量要求（ETF专用）1000万则输入 默认为0
            max_daily_money_etf 最大交易量要求（ETF专用）1000亿则输入 默认1000亿 
            N_daliy_money_etf 交易量为N天的均值（ETF专用） 默认为5天均值
        【输出】
            dataframe:date|code|ETF|cap|money
        """
        #第一步：进行是否脱机查询的判断，在线查询比较简单，直接调取jqdata相关代码即可
        if local == True:
            #脱机查询
            #定位数据库中的最后日期(这里默认使用510300进行查询)
            df_day = pd.read_sql_query(f"select * from jqdata_1d where date(date)<='{end_date.date()}' and code = '510300.XSHG' order by date desc limit 1" , self.engine)
            if df_day.empty == True:
                #数据库不存在数据
                raise ValueError(f'输入错误，请检查')
            else:
                #数据库存在数据，新定义开始日期
                last_day =  df_day.loc[0 , 'date']
                sql2 = f"select * from jqdata_security where start_date<='{end_date.date()}' and end_date >='{end_date.date()}' and type in({type})"
                try:
                    df_db = pd.read_sql_query(sql2 , self.engine)
                except:
                    print("数据读取失败")  
                #print(df_db)
                return df_db
            #【【【目前到这一步就直接返回结果，后面的代码暂时没有实装】】】
            #如果后面要去除下面代码的话，还要考虑valuation对应新增的几个索引，可以考虑删除以释放数据库空间

            #——————————————————————————————————————
            #按照条件，对所选代码进行筛选
            #1. stock 股票类数据
            #1.1 市值筛选
            #取市值表数据的最后一天
            df_val_day = pd.read_sql_query(f"select * from valuation where date(date)<='{end_date.date()}' and code = '601012.XSHG' order by date desc limit 1" , self.engine)
            if df_val_day.empty == True:
                #数据库不存在数据
                raise ValueError(f'输入错误，请检查')
            else:
                #数据库存在数据，新定义开始日期
                valuation_last_day=  df_val_day.loc[0 , 'date']
            sql_val = f"select code , date , market_cap from valuation where market_cap between {min_cap * 1e8} and {max_cap * 1e8}  and date(date) = '{valuation_last_day}'"
            print(sql_val)
            try:
                df_val = pd.read_sql_query(sql_val , self.engine)
            except:
                print("数据读取失败")  
            print(df_val)
            df_stock = df_db[(df_db['type'] == 'stock')]
                             #[( df_trans['证券代码'] == code )]
            df_stock = pd.merge(df_stock , df_val , on = ['code'], how = 'left') 
            print(df_stock)

        else:
            #在线查询，调取jqdata
            pass
           
        
