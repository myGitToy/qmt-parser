# -*- coding: utf-8 -*-
from datetime import datetime
from apt.qsp_universal.base import base
import numpy as np
import pandas as pd

"""
【分位数选股系统】


"""
class prank(base):
    def get_prank(self , N = 100 ):
        """
        获取当前bar位于前N个bar的分位数数据
        目前仅兼容60分钟线
        """
        #获取K线数据
        self.ktype = '60m'
        df = self.get_k_data()
        if df.empty == True:
            print("请检查代码%s" % (self.code))
            #本函数因为提供的dataframe 因此不能返回False 只能返回空数据
            return pd.DataFrame()
        df['p40'] = df['close'].rolling(N).quantile(0.40)
        df['p50'] = df['close'].rolling(N).quantile(0.50)
        df['p60'] = df['close'].rolling(N).quantile(0.60)
        df['p75'] = df['close'].rolling(N).quantile(0.75)
        df['p85'] = df['close'].rolling(N).quantile(0.85)
        df['p90'] = df['close'].rolling(N).quantile(0.90)
        df['p95'] = df['close'].rolling(N).quantile(0.95)
        df['code'] = self.code
        return df[['date','code','open','high','low','close','p40','p50','p60','p75','p85','p90','p95']]

    def daily_update(self , code_list = [] , N = 100 , to_csv = True):
        #ATR模块每日更新
        df_main = pd.DataFrame()
        for code in code_list:
            #循环截取所有列表中的数据
            self.code = code
            df = self.get_prank( N = N )
            df['code'] = self.code
            #日期转换为datetime64[ns] 否则会在merge操作中因为两列属性不同和无法完成合并操作
            df['date'] = pd.to_datetime(df['date'])
            df_main = pd.concat([df_main, df],sort = False)
        #保存数据
        if to_csv == True:
            #print(df_main)
            df_main.to_csv('.\\trade\\prank_jqdata.csv', encoding = 'utf_8_sig')
        return df_main