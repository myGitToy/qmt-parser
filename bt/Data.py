import backtrader as bt # 导入 Backtrader
import datetime
import pandas as pd
from apt.vendor.jqdata.jqdata import data as jqdata #jqdata的数据服务基类
from apt.vendor.jqdata.base import base as bb   #最基础的基类，用于设定服务器和授权信息
#from apt.vendor.jqdata.base import base as base
from apt.qsp_jqdata.base import base    #数据分析的基类


class Data(base):
    def init(self , server = None):
        #bt.Data的自定义设置，除非特殊指定，否则数据源默认为localhost
        if server == None :
            self.server = bb.数据源.localhost
        else:
            self.server = server

    def get_bt_data(self):
        '''
        获取Backtrader所需使用的基础数据，使用父类的get_k_data
        '''
        a = jqdata(rds_host = self.server , myauth = self.myauth)
        #此处的get_k_data从vendor.jqdata.data.get_k_data取数据，非tushare
        df = a.get_k_data(code = self.code , start_date = self.start , end_date = self.end , ktype = self.ktype , fq = self.fq)
        df = a.jqdata_to_backtrader(df)
        return df
        print(df)

    def get_trader_days(self):
        """
        获取交易日历，从基类中读取       
        """
        a = jqdata(rds_host = self.server , myauth = self.myauth)
        df = a.get_trader_days(start_date = self.start , end_date = self.end)
        return df

class CustomData_PEPB(bt.feeds.PandasData , Data ):
    """
    自定义数据投喂，可以放在Data中，也可以放在具体的策略入口中
    """
    lines = ('pe_ratio', 'market_cap', ) # 要添加的线
    # 设置 line 在数据源上的列位置
    params=(
        ('pe_ratio', -1),
        ('market_cap', -1),
           )
    # -1表示自动按列明匹配数据，也可以设置为线在数据源中列的位置索引 (('pe',6),('pb',7),)

    def add_data(self ,  code = None , df = None ):
        """
        自定义数据投喂测试模块
        获取PE/TTM（pe_ratio）和总市值数据(market_cap)
        """
        if df.empty == True:
            return df
        else:
            #进行数据处理
            #获取开始结束日期
            list = df.index
            start = list[0]
            end = list[-1]
            #start = df.iloc[0].index.values
            query2 = f"select date,pe_ratio,market_cap FROM jqdata_valuation where date(date) between {start.date()} and {end.date()} and code = {code} ORDER BY date asc" 
            df_db = pd.read_sql_query(query2 , self.engine)
            
            print(df_db)
            return df_db






