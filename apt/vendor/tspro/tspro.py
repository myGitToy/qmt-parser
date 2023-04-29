import numpy as np
import pandas as pd
import tushare as ts
from apt.vendor.tspro.base import base as base
class tspro(base):


    def get_code_list(self, list_status = 'L' , exchange = None , market = ['主板' , '中小板' , '创业板' , '科创板'] , st_filter = False , symbol = True):
        """
        获取证券代码列表（spring1只实装了创业板主板的筛选，其余交易所筛选和上市状态筛选待定）
        输入：
            list_status：上市状态（未实装） L上市 D退市 P暂停上市 A全部数据，默认L
            exchange：交易所（未实装） SSE上交所 SZSE深交所
            market:市场类型 ['主板' , '中小板' , '创业板' , '科创板'] （主板ZB/中小板ZXB/创业板CYB/科创板KCB） 不填写则默认全部
            st_filter :过滤ST代码 默认不去除
            symbol：返回代码的类型(填写True)（未实装） 默认为老代码000001 ，如果需要返回新代码000001.SZ 则symbol = False
        返回：
            list 列表类
        """
        pro = ts.pro_api()
        #不做过滤的获取全部数据导入DataFrame
        df = pro.stock_basic()
        #市场类型筛选
        df = df[df.market.isin(market)]
        if st_filter == True:
            #去除st
            code = df.loc[df['name'].str.contains('ST') == False]
            return code['symbol'].tolist() 
        else:
            code = df['symbol'].tolist() 
            return code
