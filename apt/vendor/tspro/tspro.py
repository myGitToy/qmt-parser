import numpy as np
import pandas as pd
import tushare as ts
from apt.vendor.tspro.base import base as base
class tspro(base):
    def get_code_list(self, st_filter = False):
        """
        获取证券代码列表
        输入：
            st_filter :过滤ST代码 默认不去除
        返回：
            list 列表类
        """
        pro = ts.pro_api()
        if st_filter == True:
            #不更新ST代码
            df = pro.stock_basic()
            #去除st
            code = df.loc[df['name'].str.contains('ST') == False]
            return code['symbol'].tolist() 
        else:
            code = pro.stock_basic()['symbol'].tolist() 
            return code
