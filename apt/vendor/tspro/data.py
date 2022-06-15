import numpy as np
import pandas as pd
import tushare as ts
import sqlalchemy
import akshare as ak
from datetime import datetime
from apt.vendor.jqdata.jqdata import data as jqdata
from apt.vendor.tspro.base import base as base
from apt.vendor.tspro.base import stock as stock
#应对[Errno 11003] getaddrinfo failed) 好像目前没什么用，先留着
#上述错误是因为更新sqlacademy包所引起的，目前已恢复原文件，暂时不进行升级
#import socket
#socket.getaddrinfo('localhost', 25)

class data(base,stock):
    """
    数据接口 基类
    所有需要从tusharePro获取数据的都需要从此处引用
    引用规范：from apt.vendor.jqdata.jqdata import data as jqdata
    例：量化选股 qsp_jqdata就是从这里作为基类引用的
    
    def __init__(self, rds_host=base.数据源.localhost, myauth=True , code = None , start = datetime(2021,1,1), end = datetime.now() , ktype = "1d" , fq = base.复权.动态复权 ):
        self.__init__()
        super().__init__()
        
        #super().__init__(rds_host = rds_host, myauth = myauth)
        #super().__init__(code = code , start_date = start , end_date = end , ktype = ktype , fq = fq)
    """
    #def __init__(self):
        #super(data , self).__init__()

    def update_v1(self):
        """
        tusharePro数据日常更新的主入口（按天更新）
        目前只支持日线数据更新 因为积分关系
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
                    
                    #print(df)
                    #时间日期类的列进行类型变更
                    df['date'] = pd.to_datetime(df['date'])
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

    def update_1m(self):
        """
        tusharePro1分钟数据日常更新的主入口
        目前只支持日线数据更新 因为积分关系
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
                    
                    #print(df)
                    #时间日期类的列进行类型变更
                    df['date'] = pd.to_datetime(df['date'])
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

    def get_k_data(self , code = None ,  count = None ,
                 col = ['code','date','open','close','high','low','volume','money','factor'] , 
                 flag_forward = False , ):
        
        """
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
            if self.fq == self.复权.不复权:
                if flag_forward == False:
                    #正常模式
                    return df_db.iloc[-count:][col]
                else:
                    #非正常模式，以start_date为基准输出向后的count条记录
                    return df_db.iloc[:count][col]
            elif self.fq ==self.复权.前复权:
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
            elif self.fq ==self.复权.后复权:
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
            elif self.fq ==self.复权.动态复权:
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
    #测试ak复权因子
    a = data()
    jq = jqdata()
    a.code ='600038.sh'
    a.start_date= datetime(2010,1,1)
    a.end_date = datetime(2010,11,26)
    dt = a.get_ak_factor()
    print(dt[0])
    print(f"最后一个复权因子为{dt[1]}")
    df = a.get_k_data()
    print(df[['code','date','open','close','high','low','volume','money','factor']])
    df_jq = jq.get_k_data(code  = '600038.XSHG' , start_date = a.start_date , end_date = a.end_date)
    print(df_jq[['code','date','open','close','high','low','volume','money','factor']])
    
    #获取需要更新的证券列表
    pro = ts.pro_api('55297f16c0119146589e059db315ba28a9412e89ec9f91e538e655b2')
    # 拉取数据
    #df = pro.daily(ts_code = '600038.SH' , start_date = '2022/1/1')
    df = pro.daily(trade_date= '20220602')

    #df = pro.daily(ts_code='000001.SZ', start_date='20180701', end_date='20180718')
    #code = pro.daily(trade_date='20200918')['ts_code'].apply(lambda x:x[:6]).tolist()
    #df['trade_date'] = pd.to_datetime(df['trade_date'])
    print(df)
   