# -*- coding: utf-8 -*-
from  apt.os.data_load import Data_Load as dl
from  apt.os.data_update import Data_Update as update
from datetime import datetime
from apt.qsp_jqdata.base import base
import numpy as np
import pandas as pd
"""
【ATR技术分析系统】
"""
class ATR(base):
    def get_atr(self , N = 20 , MAHR_100_HIGH = 20, MAHR_20 = 5 ,MAHR_30 = 8):
        """
        计算ATR数值
        输入：
            N: ATR的计算周期 默认20天移动平均线（即NTR计算的周期，以多少个每日TR来计算当前的ATR）
            MAHR_100_HIGH 小时线100小时最高价格 对应到日线为20天线最高价格 正常情况下无需更改
            MAHR_20: 小时线20小时均线价格 对应到日线为5天线 正常情况下无需更改
            MAHR_30: 小时线30小时均线价格 对应到日线为7.5天，近似成8天线 正常情况下无需更改        
        返回：
            带有ATR内容的DataFrame 除正常日线数据外，还输出TR ATR MAHR_100_HIGH MAHR_20 MAHR_30
        存在的问题：
        """
        #获取K线数据
        df = self.get_k_data()
        if df.empty == True:
            print("请检查代码%s" % (self.code))
            #本函数因为提供的dataframe 因此不能返回False 只能返回空数据
            return pd.DataFrame()
        df['close_1'] = df['close'].shift(1)
        #使用max函数会报错，目前措施是新建列，为上一天的收盘价，和当天的数据做对齐，随后进行计算和比较  max(df['high'],df['close'].shift(1)
        #另外第一列数据对齐后会出现NA用上述方法执行后比对不会出错
        df['TR'] = df[['high','close_1']].max(axis=1) - df[['low','close_1']].min(axis=1)
        #ATR移动平均线计算
        df['ATR'] = df['TR'].rolling(N).mean()
        #小时线100小时最高收盘价计算
        df['MAHR_100_HIGH'] = df['high'].rolling(MAHR_100_HIGH).max()
        #小时线20小时均线价格计算
        df['MAHR_20'] = df['close'].rolling(MAHR_20).mean()
        #小时线30小时均线价格
        df['MAHR_30'] = df['close'].rolling(MAHR_30).mean()
        #小时线100小时ATR偏离
        df['MAHR_100_HIGH_DEV'] = (df['close'] - df['MAHR_100_HIGH']) / df['ATR']
        #小时线20小时均线ATR偏离
        df['MAHR_20_DEV'] = (df['close'] - df['MAHR_20']) / df['ATR']
        ##小时线30小时均线ATR偏离
        df['MAHR_30_DEV'] = (df['close'] - df['MAHR_30']) / df['ATR']
        #print(df[['date','close','ATR']])
        return df

