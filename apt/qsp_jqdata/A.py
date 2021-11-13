# -*- coding: utf-8 -*-
from datetime import datetime
from apt.qsp_jqdata.base import base
from apt.vendor.jqdata.jqdata import data as data
import numpy as np
import pandas as pd
import talib as ta
"""
【选股系统A jqdata】
目录树：
    A01
    A02
    A03
    A04 EXPMA选股系统
"""
class A(base):
    def A04B01_EMA均线数据(self , ma_list = ['5','10','20','30','60','120']):
        """
        EXPMA选股系统
        输入：
            证券代码，起止日期按照默认
            ma_list：需计算的均线 ['5','10','20','30','60','120']
        输出：DataFrame 各均线价格 列的规范：EMA5|EMA60|EMA120
        """
        #df = self.get_k_data( code = self.code , start_date= self.start , end_date= self.end , ktype= self.ktype)
        df = self.get_k_data()
        for ma in ma_list:
            df[f'EMA{ma}'] = ta.EMA(df['close'] ,  timeperiod = int(ma))
        return df

    def A04B02_EMA均线多头排列(self , ma_list = ['10','20','30','60','120']):
        """
        EXPMA选股系统
        输入：
            证券代码，起止日期按照默认
            ma_list：需计算的均线 ['10','20','30','60','120']
        输出：T/F
        """
        #df = self.get_k_data( code = self.code , start_date= self.start , end_date= self.end , ktype= self.ktype)
        df = self.get_k_data()
        df['ema5'] = ta.EMA(df['close'] ,  timeperiod=60)
        print(df)

