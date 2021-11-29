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




