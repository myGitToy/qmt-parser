import numpy as np
import pandas as pd
import tushare as ts
import sqlalchemy
import time
#from apt.qsp_universal.base import base as kdata
#from apt.vendor.akshare.base import base as akdata
#import datetime
from scipy import stats
from datetime import datetime,timedelta
from jqdatasdk import *
#from apt.vendor.tspro.base import base as base
from apt.vendor.tspro.data import data as tspro_data
from apt.vendor.tspro.security import security as sec

class money_flow(tspro_data):
    """
    专门处理资金流向的类
    模块的结构说明文档详见
    https://huiqiao.visualstudio.com/MyFunds/_sprints/taskboard/MyFunds%20Team/MyFunds/2023Q3?workitem=489
    """
    #def __init__(self):
        #声明父类的init方法，也可以选择不声明
        #super().__init__()

    def daily_update(self , sleep = 0.2):
        """
        每日资金流向更新（按日更新）
        原始jqdata是按代码更新的，新逻辑按日期进行更新   
        数据起始日期为2007年(2007年上半年的数据不太稳定，有部分日期缺失)
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
        #print(day_diff)
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

    def get_money_flow(self , rolling_list = [3,5,10,20,30,60,120] , to_excel = False):
        """
        获取资金流向(tspro资金流向) 
        ['3','5','10','20','30','60','120']
        各类别统计规则如下：
        小单：5万以下 中单：5万～20万 大单：20万～100万 特大单：成交额>=100万
        只能按照日线数据获取        
        输入：
            rolling_list 需要回滚的日期列表
            to_excel 是否保存到excel文档（这里没想好是excel文件还是csv文件）
        返回：
            DataFrame
        """
        #获取基础信息

        #判断是否是stock类型 且有数据
        if  sec.get_security(self , code = self.code)[1] !='stock':
            raise ValueError(f'请检查证券代码:{self.code}非stock类代码')

        #获取K线数据
        #df =data.get_k_data(self)
        #获取流通市值信息
        #df_val = pd.read_sql_query(f"select code,date,circulating_market_cap from valuation where code = '{code}' order BY date" , self.engine)
        #df = pd.merge(df,df_val,on = ['code','date']) 

        #获取资金流向
        df = pd.read_sql_query(f"select * from tspro_money_flow where code = '{self.code}' and date between '{self.start_date.date()}' and '{self.end_date.date()}' order BY date" , self.engine)
        #df = pd.merge(df,df_money_flow,on = ['code','date']) 
        #基础资金流向列表的计算
        df['小单净额'] = df['buy_sm_amount'] - df['sell_sm_amount']
        df['中单净额'] = df['buy_md_amount'] - df['sell_md_amount']
        df['大单净额'] = df['buy_lg_amount'] - df['sell_lg_amount']
        df['超单大净额'] = df['buy_elg_amount'] - df['sell_elg_amount']
        df['散户净额'] = df['小单净额'] + df['中单净额']
        df['主力净额'] = df['大单净额'] + df['超单大净额']
        for n in rolling_list:
            #滚动窗口累计计算
            #df[f'小单金额_r{n}'] = df['小单净额'].rolling(n).mean().apply(lambda x: '%.2f'%x)  #小数点截取范例
            df[f'小单金额_r{n}'] = df['小单净额'].rolling(n).sum()
            df[f'中单净额_r{n}'] = df['中单净额'].rolling(n).sum()
            df[f'大单净额_r{n}'] = df['大单净额'].rolling(n).sum()
            df[f'超单大净额_r{n}'] = df['超单大净额'].rolling(n).sum()
            df[f'散户净额_r{n}'] = df['散户净额'].rolling(n).sum()
            df[f'主力净额_r{n}'] = df['主力净额'].rolling(n).sum()
            #滚动窗口
            df[f'小单金额_p{n}'] =  df[f'小单金额_r{n}'].rolling(n).apply(lambda x: stats.percentileofscore(x, x.iloc[-1]))
            df[f'中单净额_p{n}'] =  df[f'中单净额_r{n}'].rolling(n).apply(lambda x: stats.percentileofscore(x, x.iloc[-1]))
            df[f'大单净额_p{n}'] =  df[f'大单净额_r{n}'].rolling(n).apply(lambda x: stats.percentileofscore(x, x.iloc[-1]))
            df[f'超单大净额_p{n}'] =  df[f'超单大净额_r{n}'].rolling(n).apply(lambda x: stats.percentileofscore(x, x.iloc[-1]))
            df[f'散户净额_p{n}'] =  df[f'散户净额_r{n}'].rolling(n).apply(lambda x: stats.percentileofscore(x, x.iloc[-1]))
            df[f'主力净额_p{n}'] =  df[f'主力净额_r{n}'].rolling(n).apply(lambda x: stats.percentileofscore(x, x.iloc[-1]))
            #设置格式（格式设置会使输出的数字采用文本方式保存，所以这里暂时不启用）
            #df[f'小单金额_p{n}'] =  df[f'小单金额_p{n}'].apply(lambda x: '%.2f'%x) 
            #df[f'中单净额_p{n}'] =  df[f'中单净额_p{n}'].apply(lambda x: '%.2f'%x) 
            #df[f'大单净额_p{n}'] =  df[f'大单净额_p{n}'].apply(lambda x: '%.2f'%x) 
            #df[f'超单大净额_p{n}'] =  df[f'超单大净额_p{n}'].apply(lambda x: '%.2f'%x) 
            #df[f'散户净额_p{n}'] =  df[f'散户净额_p{n}'].apply(lambda x: '%.2f'%x) 
            #df[f'主力净额_p{n}'] =  df[f'主力净额_p{n}'].apply(lambda x: '%.2f'%x) 
        if to_excel ==True:
            #输出EXCEL
            df.to_excel(f'.\\data\\测试数据\\资金流向{self.code}.xlsx', sheet_name = f'sheet1' ,  header=True, index=False)
        return df
        #回滚N天进行计算
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
            df.to_excel(f'.\\data\\测试数据\\资金流向{self.code}.xlsx', sheet_name = f'sheet1' ,  header=True, index=False)

        #返回DataFrame
        return df
        #合并文件
        df_main = pd.concat([df_main, df],sort = False)

    def get_money_flow_v2(self , to_excel = False):
        """
        获取资金流向(1min数据计算而来) 
        """
        #获取基础信息

        #判断是否是stock类型 且有数据
        if  sec.get_security(self , code = self.code)[1] !='stock':
            raise ValueError(f'请检查证券代码:{self.code}非stock类代码')
        
        #获取K线数据
        d = akdata()
        d.code = self.code
        d.start_date = self.start_date
        d.end_date = self.end_date
        d.ktype = self.ktype
        #d.vendor = self.vendor
        df_db = d.get_k_data()
        print(df_db)
        #df_db = d.get_k_data(self)
        #获取流通市值信息
        #df_val = pd.read_sql_query(f"select code,date,circulating_market_cap from valuation where code = '{code}' order BY date" , self.engine)
        #df = pd.merge(df,df_val,on = ['code','date']) 

        #获取资金流向
        df = pd.read_sql_query(f"select * from tspro_money_flow where code = '{self.code}' and date between '{self.start_date.date()}' and '{self.end_date.date()}' order BY date" , self.engine)
        #df = pd.merge(df,df_money_flow,on = ['code','date']) 
        #基础资金流向列表的计算
        df['小单净额'] = df['buy_sm_amount'] - df['sell_sm_amount']
        df['中单净额'] = df['buy_md_amount'] - df['sell_md_amount']
        df['大单净额'] = df['buy_lg_amount'] - df['sell_lg_amount']
        df['超单大净额'] = df['buy_elg_amount'] - df['sell_elg_amount']
        df['散户净额'] = df['小单净额'] + df['中单净额']
        df['主力净额'] = df['大单净额'] + df['超单大净额']

    def __get_1min_flow(self , code = '600001.sh' , day = datetime(2023,1,1)):
        """
        获取资金流向(1分钟数据) 
        从akshare 1分钟线价格 成交量转换过来的资金流向（单日资金流向）
        注意：这里用的是1分钟线，因此采用的是akdata数据
        【输入】：
            code 证券代码
            day 交易日期
        【输出】
        """
        #交易日检查（暂未开通）
        #self.code = code 
        #self.end_date = day
        #self.ktype = '1m'

        #a = base()
        #a.code = code
        #a.start_date = day.date() + timedelta(hours = 8)
        #a.end_date = day.date() + timedelta(hours = 16)
        #a.ktype = self.ktype
        #a.vendor = self.vendor
        df = self.get_k_data().sort_values(by = ['date'] )
        print(df)
        #删除9:30和15:00的数据
        df = df.query('date.dt.time != datetime.strptime("09:30","%H:%M").time()')
        df = df.query('date.dt.time != datetime.strptime("15:00","%H:%M").time()')
        df['close_diff'] = df['close'] - df['close'].shift(1)
        #np.where单独使用，符合条件的返回array组，再使用iloc进行定位和修订
        df['money_flow'] = np.nan
        #df.iloc[np.where(df['close_diff'] > 0)]['money_flow'] = 1
        df['money_flow'] = np.where(df['close_diff'] > 0 , df['money'] , df['money_flow'] )
        df['money_flow'] = np.where(df['close_diff'] < 0 , -df['money'] , df['money_flow'] )
        df['money_flow'] = np.where(df['close_diff'] == 0 , 0 , df['money_flow'] )
        df['cumsum'] = df['money_flow'].cumsum()
        print(df)
        # 对时间进行一下处理
        df['date'] = pd.to_datetime(df['date'],format = "%m-%d")
        df.set_index('date',inplace=True)
        #print(df[['date','close','close_diff','money','money_flow','cumsum']])
        #统一各股资金流向的坐标轴，统一按照1个million来计算，也就是对应的1e7
        df['cumsum'] = df['cumsum'] / 1000000
        num = df.iloc[-1].at['cumsum']
        return num      
if __name__=="__main__":
    #此模块用于历史数据的更新，目前2021年前的数据已完成更新，因此模块下架停止使用
    money = money_flow()
    money.code = '600519.sh'
    money.start_date = datetime(2021,1,1)
    money.end_date = datetime(2023,7,31)
    money.ktype = '1m'
    df = money.get_money_flow()
    print(df)
    money.start_date = datetime(2021,1,1) 
    money.end_date = datetime(2023,7,26)
    money.daily_update(sleep = 0.2)