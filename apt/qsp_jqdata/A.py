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
    A01 MA均线选股系统
    A02
    A03
    A04 EXPMA均线选股系统
"""
class A(base):
    def A01B01_MA均线数据(self , ma_list = ['5','10','20','30','60','120']):
        """
        ]MA选股系统
        输入：
            证券代码，起止日期按照默认
            ma_list：需计算的均线 ['5','10','20','30','60','120']
        输出：DataFrame 各均线价格 列的规范：MA5|MA60|MA120
        """
        #df = self.get_k_data( code = self.code , start_date= self.start , end_date= self.end , ktype= self.ktype)
        df = self.get_k_data()
        for ma in ma_list:
            df[f'MA{ma}'] = ta.MA(df['close'] ,  timeperiod = int(ma))
        return df

    def A01B02_MA均线多头排列(self , ma_list = ['10','20','60','120']):
        """
        MA均线多头排列
        输入：
            证券代码，起止日期按照默认
            ma_list：需计算的均线 ['10','30','60','120']
        输出：T/F
        """
        df = self.A01B01_MA均线数据(ma_list = ma_list)
        #多头排列 Bull Market
        #判断ma均线的个数        
        count = len(ma_list)
        for n in range(0 , count - 1):
            short = df.iloc[-1].at[f'MA{ma_list[n]}']
            long = df.iloc[-1].at[f'MA{ma_list[n+1]}']
            if  short < long:
                return False
        return True
        
    def A01B03_MA均线空头排列(self , ma_list = ['10','20','60','120']):
        """
        MA均线空头排列
        输入：
            证券代码，起止日期按照默认
            ma_list：需计算的均线 ['10','30','60','120']
        输出：T/F
        """
        df = self.A01B01_MA均线数据(ma_list = ma_list)
        #空头排列 Bear Market
        #判断ma均线的个数        
        count = len(ma_list)
        for n in range(0 , count - 1):
            short = df.iloc[-1].at[f'MA{ma_list[n]}']
            long = df.iloc[-1].at[f'MA{ma_list[n+1]}']
            if  short > long:
                return False
        return True

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

    def A04B02_EMA均线多头排列(self , ma_list = ['10','20','60','120']):
        """
        EMA均线多头排列
        输入：
            证券代码，起止日期按照默认
            ma_list：需计算的均线 ['10','30','60','120']
        输出：T/F
        """
        df = self.A04B01_EMA均线数据(ma_list = ma_list)
        #多头排列 Bull Market
        #判断ma均线的个数        
        count = len(ma_list)
        for n in range(0 , count - 1):
            short = df.iloc[-1].at[f'EMA{ma_list[n]}']
            long = df.iloc[-1].at[f'EMA{ma_list[n+1]}']
            if  short < long:
                return False
        return True
        
    def A04B03_EMA均线空头排列(self , ma_list = ['10','20','60','120']):
        """
        EMA均线空头排列
        输入：
            证券代码，起止日期按照默认
            ma_list：需计算的均线 ['10','30','60','120']
        输出：T/F
        """
        df = self.A04B01_EMA均线数据(ma_list = ma_list)
        #空头排列 Bear Market
        #判断ma均线的个数        
        count = len(ma_list)
        for n in range(0 , count - 1):
            short = df.iloc[-1].at[f'EMA{ma_list[n]}']
            long = df.iloc[-1].at[f'EMA{ma_list[n+1]}']
            if  short > long:
                return False
        return True

    def A04B04_EMA均线_收盘价大于均线(self , ma= '10' , adjust_N = 1 , count = 1):
        """
        收盘价大于某条EMA均线
        输入：
            证券代码，起止日期按照默认
            ma：某条均线 默认为10日均线
            adjust_N : N天内符合条件就返回T 默认为当天
            count: N天内符合count次就返回True 默认为1
            例子：最后一个交易日收盘价大于EMA均线  adjust_ N = 1 ; count = 1
                    最后5个交易日出现2次大于EMA均线 adjust_ N = 5 ; count = 2
                    最后7个交易日每日收盘价均高于EMA均线 adjust_ N = 7 ; count = 7
        输出：T/F
        """
        lst = []
        lst.append(ma)
        df = self.A04B01_EMA均线数据(ma_list = lst)
        #丢弃NA数据，如果该列为NA，则返回是B 即收盘价小于EMA的NA数据
        df.dropna(how = 'any' , inplace = True)
        #如果数据量不足，返回False
        if df.empty == True:
            return False
        #A代表收盘价大于EMA均线，B代表收盘价小于EMA均线
        df['position'] = np.where(df['close'] >= df[f'EMA{ma}'] , 'A' , 'B')
        #下面这个方法也是可以的
        #df.loc[df['close'] >= df['EMA120'],['position2']] = 'A'
        #截取最后adjust_N的矩阵
        df = df[-adjust_N :]
        #print(df)
        #print(df['position'].isin(['A']))  返回是否包含A T/F
        #获取A出现的次数
        try:
            cc = df['position'].value_counts()['A']
        except:
            cc = 0
        #如果A次数大于目标值(count) 返回True
        if cc >= count:
            return True
        else:
            return False

    def A04B05_EMA均线_收盘价小于均线(self , ma= '10' , adjust_N = 1 , count = 1):
        """
        收盘价小于某条EMA均线
        输入：
            证券代码，起止日期按照默认
            ma：某条均线 默认为10日均线
            adjust_N : N天内符合条件就返回T 默认为当天
            count: N天内符合count次就返回True 默认为1
            例子：最后一个交易日收盘价小于EMA均线  adjust_ N = 1 ; count = 1
                    最后5个交易日出现2次小于EMA均线 adjust_ N = 5 ; count = 2
                    最后7个交易日每日收盘价均小于EMA均线 adjust_ N = 7 ; count = 7
        输出：T/F
        """
        lst = []
        lst.append(ma)
        df = self.A04B01_EMA均线数据(ma_list = lst)
        #丢弃NA数据，如果该列为NA，则返回是B 即收盘价小于EMA的NA数据
        df.dropna(how = 'any' , inplace = True)
        #如果数据量不足，返回False
        if df.empty == True:
            return False
        #A代表收盘价大于EMA均线，B代表收盘价小于EMA均线
        df['position'] = np.where(df['close'] >= df[f'EMA{ma}'] , 'A' , 'B')
        #下面这个方法也是可以的
        #df.loc[df['close'] >= df['EMA120'],['position2']] = 'A'
        #截取最后adjust_N的矩阵
        df = df[-adjust_N :]
        #print(df)
        #print(df['position'].isin(['A']))  返回是否包含A T/F
        #获取B出现的次数
        try:
            cc = df['position'].value_counts()['B']
        except:
            cc = 0
        #如果A次数大于目标值(count) 返回True
        if cc >= count:
            return True
        else:
            return False


