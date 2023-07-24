import numpy as np
import pandas as pd
import tushare as ts
import sqlalchemy
import time
#import datetime
from datetime import datetime,timedelta
from jqdatasdk import *
from apt.vendor.tspro.base import base as base
from apt.vendor.tspro.data import data as data
from apt.vendor.tspro.security import security as sec

class money_flow(base):
    """
    专门处理资金流向的类
    """
    def daily_update(self , sleep = 0.5 ):
        """
        每日资金流向更新（按日更新）
        原始jqdata是按代码更新的
        数据起始日期为2007年(2007年上半年的数据不太稳定，有部分日期缺失)
        2010-01-04 数据已上传完成，更新条目数834 (money flow)
        2010-01-05 数据已上传完成，更新条目数1627 (money flow)
        数据有突变
        """
        #获取更新列表（按交易日）
        se = sec()
        se.start_date = self.start_date
        se.end_date = self.end_date
        trade_day = pd.DataFrame(columns = ['date'])
        trade_day = se.get_calendar(is_open = 1)
        #获取资金流向库中存在的日期列表
        query_daysql = f"select distinct date FROM tspro_money_flow FORCE INDEX (main) WHERE date BETWEEN '{self.start_date.date()}' and '{self.end_date.date()}'  ORDER BY date asc" 
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
        print("############正在准备更新资金流向信息###########")
        """
        更新逻辑：
            1. 需要更新的日期
                1.1 取出区间内的交易日
                1.2 取出数据库中存在资金流向的日期
                1.3 两者取差集就是需要更新的日期
            2. 按照日期循环，获取每日的资金流向
            3. 数据写入数据库
        逻辑优点和不足：
            1. 一次性提取每日的资金流向，运行效率较高
            2. 智能化更新，跳过重复的日期
            3. 缺点：更新限制每次5000条，后续可能会超过限制值
        """
        for day in day_diff['date']:
            #获取数据库中存在的数据最后更新日期（加入强制使用索引的内容）
            df = self.pro.moneyflow(trade_date = day.strftime("%Y%m%d"))
            #重命名列（money_flow中的证券代码sec_code和数据库中的不一致）
            df.rename(columns = {'ts_code':'code','trade_date':'date'} , inplace = True)
            df['date'] = pd.to_datetime(df['date']) #时间日期ns64化
            #保存至数据库 
            if df.empty == True:
                print(f"{day.date()}数据为空，跳过上传")
            else:
                df.to_sql(
                        name = 'tspro_money_flow',
                        con = self.engine,
                        index = False,
                        if_exists = 'append')
                print(f"{day.date()} 数据已上传完成，更新条目数{df.shape[0]} (money flow)")
                time.sleep(sleep)

    def get_money_flow(self , code =  None , start_date = datetime(2010,1,1) , end_date = datetime.now() , column_name = '' , ma = 5 , to_excel = True):
        """
        获取资金流向(本地数据库) 
        只能按照日线数据获取
        输入：
            code 证券代码
            start_date 开始日期
            end_date 结束日期
            ma 资金流向需要取N天的平均数据
        返回：
            DataFrame
        """
        #获取基础信息

        #判断是否是stock类型 且有数据
        if  data.get_code_type(self , code = code) !='stock':
            raise ValueError(f'请检查证券代码{code}')

        #获取K线数据
        df =data.get_k_data(self , code = code , start_date = start_date, end_date = end_date , ktype  = '1d' )
        #获取流通市值信息
        df_val = pd.read_sql_query(f"select code,date,circulating_market_cap from valuation where code = '{code}' order BY date" , self.engine)
        df = pd.merge(df,df_val,on = ['code','date']) 

        #获取资金流向
        df_money_flow = pd.read_sql_query(f"select code,date,net_amount_main as main,net_amount_xl as xl,net_amount_l as l,net_amount_m as m,net_amount_s as s from jqdata_money_flow where code = '{code}' order BY date" , self.engine)
        df = pd.merge(df,df_money_flow,on = ['code','date']) 

        #资金流向N日平均值
        df[f'main{ma}'] = df['main'].rolling(ma).mean()
        df[f'xl{ma}'] = df['xl'].rolling(ma).mean()
        df[f'l{ma}'] = df['l'].rolling(ma).mean()
        df[f'm{ma}'] = df['m'].rolling(ma).mean()
        df[f's{ma}'] = df['s'].rolling(ma).mean()

        #N资金与流通市值占比
        df[f'main{ma}_cap'] = df[f'main{ma}'] / df['circulating_market_cap'] / 10000
        df[f'xl{ma}_cap'] = df[f'xl{ma}'] / df['circulating_market_cap'] / 10000
        df[f'l{ma}_cap'] = df[f'l{ma}'] / df['circulating_market_cap'] / 10000
        df[f'm{ma}_cap'] = df[f'm{ma}'] / df['circulating_market_cap'] / 10000
        df[f's{ma}_cap'] = df[f's{ma}'] / df['circulating_market_cap'] / 10000

        if to_excel ==True:
            #输出EXCEL
            df.to_excel(f'.\\data\\测试数据\\资金流向{code}.xlsx', sheet_name = f'sheet1' ,  header=True, index=False)

        #返回DataFrame
        return df
        #合并文件
        df_main = pd.concat([df_main, df],sort = False)


if __name__=="__main__":
    #此模块用于历史数据的更新，目前2021年前的数据已完成更新，因此模块下架停止使用
    money = money_flow()
    money.start_date = datetime(2016,1,1)
    money.end_date = datetime(2023,7,24)
    money.daily_update(sleep = 0.2)