# -*- coding: utf-8 -*-
from datetime import datetime
from apt.qsp_universal.base import base
from apt.qsp_universal.A import A as A
import numpy as np
import pandas as pd

"""
【EMA系统】
"""
class expma(base):
    def daily_update(self , code_list = [] , N = 100 , to_csv = True):
        #EXPMA模块每日更新
        df_main = pd.DataFrame()
        for code in code_list:
            #循环截取所有列表中的数据
            a = A()
            a.code = code
            a.start_date = self.start_date
            a.end_date = self.end_date
            a.ktype = self.ktype
            a.vendor = self.vendor
            df = a.A04B01_EMA均线数据()
            #日期转换为datetime64[ns] 否则会在merge操作中因为两列属性不同和无法完成合并操作
            df['date'] = pd.to_datetime(df['date'])
            df_main = pd.concat([df_main, df] , sort = False)
        #保存数据
        if to_csv == True:
            df_main.to_csv(f'.\\data\\海龟模型\\expma_{self.vendor}.csv', encoding = 'utf_8_sig')
        return df_main