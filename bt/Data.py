from apt.vendor.jqdata.jqdata import data as jqdata

class Data(jqdata):
    def get_bt_data(self):
        '''
        获取Backtrader所需使用的基础数据，使用父类的get_k_data
        '''
        df = self.get_k_data()
        print(df)


