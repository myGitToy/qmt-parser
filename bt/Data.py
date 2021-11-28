from apt.vendor.jqdata.jqdata import data as jqdata
#from apt.vendor.jqdata.base import base as base
from apt.qsp_jqdata.base import base
class Data(base):
    def get_bt_data(self):
        '''
        获取Backtrader所需使用的基础数据，使用父类的get_k_data
        '''
        a = jqdata(myauth = self.myauth)
        #此处的get_k_data从vendor.jqdata.data.get_k_data取数据，非tushare
        df = a.get_k_data(code = self.code , start_date = self.start , end_date = self.end , ktype = self.ktype , fq = self.fq)
        df = a.jqdata_to_backtrader(df)
        return df
        print(df)


