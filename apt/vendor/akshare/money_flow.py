import numpy as np
import pandas as pd
import tushare as ts
import akshare as ak
import sqlalchemy
from scipy import stats
from datetime import datetime
#from apt.vendor.akshare.base import base as base
#from apt.vendor.akshare.base import stock as stock
from apt.vendor.akshare.data import data as akdata
from apt.vendor.tspro.money_flow import money_flow as ts_flow
from sqlalchemy.types import NVARCHAR , Float, Integer , Date
from apt.vendor.tspro.security import security as sec

class money_flow(akdata):
    """
    专门处理资金流向的类
    两种不同的资金流向：V1. 从tspro获取的传统资金流向（联网通过API方式）
                        V2. 从akshare 1分钟线价格 成交量转换过来的资金流向（从数据库获取）
    """
    def daily_update(self , sleep = 0.2):
        """
        每日资金流向更新（按日更新）
        此处实际调用vendor.tspro下面的方法
        """
        #获取更新列表（按交易日）
        return ts_flow.daily_update(self , sleep = sleep)

    def get_money_flow(self , rolling_list = [3,5,10,20,30,60,120] , to_excel = False):
        """
        获取资金流向(tspro资金流向) 
        此处实际调用vendor.tspro下面的方法
        """
        return ts_flow.get_money_flow(self , rolling_list = rolling_list , to_excel = to_excel)

    def get_money_flow_1min(self , rolling_list = [3,5,10,20,30,60,120] , to_excel = False):
        """
        从akshare 1分钟线价格 成交量转换过来的资金流向
        【输入】
            self.code 证券代码
            day 日期
        【返回】
            单个代码在指定日期区间的资金流向（万元）
        """
        #交易代码校验（跳过）
        #原因：1分钟线数据支持stock类和etf类
        #获取数据（强制使用1分钟线）
        self.ktype = '1m'
        df_db = self.get_k_data().sort_values(by = ['date'] )
        #初始化最后需要输出的DataFrame
        df_flow = pd.DataFrame(columns = [['money_flow']], index = df_db['date'].dt.date.unique())
        #distinct_dates['date'] = df_db['date'].dt.date.unique()
        #distinct_dates['date'] = pd.to_datetime(df_db['date'].dt.date.unique()) #时间日期ns64化
        series_days = df_db['date'].dt.date.unique()
        #print(distinct_dates.shape[0])
        for day in series_days:
            #print(day)
            df = df_db.query('date.dt.date == @day')
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
            df_flow.loc[day,'money_flow'] = df.iloc[-1]['cumsum'] /10000
            #print(distinct_dates)
        #对输出的df进行调整，列 code|date|money_flow
        df_flow['code'] = self.code
        df_flow = df_flow.rename_axis('date').reset_index()
        #df_flow['money_flow'] = df_flow['money_flow'].apply(lambda x: format(x, '.2f'))
        #df_flow['date'] = pd.to_datetime(df_flow['date'])
        #print(df_flow)
        #基础资金流向列表的计算
        for n in rolling_list:
            #滚动窗口累计计算
            df_flow[f'money_flow_r{n}'] = df_flow['money_flow'].rolling(n).sum()
            #分位数计算
            df_flow[f'money_flow_p{n}'] =  df_flow[f'money_flow_r{n}'].rolling(n).apply(lambda x: stats.percentileofscore(x, x.iloc[-1]))
        if to_excel ==True:
            #输出EXCEL
            df_flow.to_excel(f'.\\data\\测试数据\\资金流向_1min_{self.code}.xlsx', sheet_name = f'sheet1' ,  header = True, index = True)
        #print(df_flow)
        return df_flow


               
if __name__=="__main__":
    #测试资金流向
    money = money_flow()
    money.code = '688349.sh'
    money.start_date = datetime(2021,1,1)
    money.end_date = datetime(2023,8,5)
    money.daily_update()
    money.ktype = '1d'
    df = money.get_money_flow_1min(to_excel = True ,rolling_list = [10,20])
    print(df)

    