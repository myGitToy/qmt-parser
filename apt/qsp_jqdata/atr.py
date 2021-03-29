# -*- coding: utf-8 -*-
from datetime import datetime
from apt.qsp_jqdata.base import base
import numpy as np
import pandas as pd
"""
【ATR技术分析系统】
"""
class ATR(base):
    def get_atr(self , N = 20 , MAHR_100_HIGH = 25, MAHR_20 = 5 ,MAHR_30 = 8):
        """计算ATR
        输入：
            ATR_MA ATR的计算周期 默认20天移动平均线（2021/1/6修改到14天）
            MAHR_100_HIGH 小时线100小时最高价格 对应到日线为25天线最高价格 正常情况下无需更改（2021/1/6修改到20天）
            MAHR_20: 小时线20小时均线价格 对应到日线为5天线 正常情况下无需更改
            MAHR_30: 小时线30小时均线价格 对应到日线为7.5天，近似成8天线 正常情况下无需更改
        输出：除正常日线数据外，还输出
            TR: 当日波动 
            ATR: 连续N天波动，N = 20天 由 MA_ATR控制
            MAHR_100_HIGH：N天内最高价（收盘价或者最高价 目前逻辑中指定为最高价）
            MAHR_20：N小时均线 N = 20小时/5天
            MAHR_30：N小时均线 N = 30小时/8天
            MAHR_100_HIGH_DEV：N天内最高价格ATR偏离程度 N = 100小时/25天
            MAHR_20_DEV：20小时（5天线）均线ATR偏离程度（收盘价） 
            MAHR_30_DEV：30小时（8天线）均线ATR偏离程度（收盘价）
            MAHR_20_LOW_DEV（过渡列，不进行输出）：20小时（5天线）均线ATR偏离程度（最低价）
            MAHR_30_LOW_DEV（过渡列，不进行输出）：30小时（8天线）均线ATR偏离程度（最低价）
            MAX_MAHR_20_DEV：N周期内，20小时（5天线）均线最大ATR偏离程度（最低价） N =  MAHR_100_HIGH / 2
            MAX_MAHR_30_DEV：N周期内，30小时（8天线）均线最大ATR偏离程度（最低价） N =  MAHR_100_HIGH / 2
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
        #ATR移动平均线计算（这里能计算SMA简单移动平均线 ，如果要计算EMA则需要引入talib）
        df['ATR'] = df['TR'].rolling(N).mean()
        #小时线100小时最高收盘价计算
        df['MAHR_100_HIGH'] = df['close'].rolling(MAHR_100_HIGH).max()
        #小时线20小时均线价格计算
        df['MAHR_20'] = df['close'].rolling(MAHR_20).mean()
        #小时线30小时均线价格
        df['MAHR_30'] = df['close'].rolling(MAHR_30).mean()
        #小时线100小时ATR偏离
        df['MAHR_100_HIGH_DEV'] = (df['close'] - df['MAHR_100_HIGH']) / df['ATR']
        #小时线20小时均线ATR偏离
        df['MAHR_20_DEV'] = (df['close'] - df['MAHR_20']) / df['ATR']
        #小时线20小时的最低价格对于均线的ATR偏离程度
        df['MAHR_20_LOW_DEV'] = (df['low'] - df['MAHR_20']) / df['ATR']
        #小时线20小时均线ATR偏离最大值（周期为MAHR_100_HIGH）
        df['MAX_MAHR_20_LOW_DEV'] = df['MAHR_20_LOW_DEV'].rolling(int(MAHR_100_HIGH / 2)).min()
        ##小时线30小时均线ATR偏离
        df['MAHR_30_DEV'] = (df['close'] - df['MAHR_30']) / df['ATR']
        #小时线30小时的最低价格对于均线的ATR偏离程度
        df['MAHR_30_LOW_DEV'] = (df['low'] - df['MAHR_30']) / df['ATR']
        #小时线30小时的最低价格对于均线的ATR偏离程度（周期为MAHR_100_HIGH）
        df['MAX_MAHR_30_LOW_DEV'] = df['MAHR_30_LOW_DEV'].rolling(int(MAHR_100_HIGH / 2)).min()
        #print(df[['date','close','ATR']])
        return df

    def daily_update(self , code_list = [] , N = 20 , MAHR_100_HIGH = 25, MAHR_20 = 5 ,MAHR_30 = 8 , to_csv = True):
        #ATR模块每日更新
        df_main=pd.DataFrame()
        for code in code_list:
            #循环截取所有列表中的数据
            self.code = code
            df = self.get_atr( N = N , MAHR_100_HIGH = MAHR_100_HIGH, MAHR_20 = MAHR_20 ,MAHR_30 = MAHR_30 )
            df['code'] = self.code
            #日期转换为datetime64[ns] 否则会在merge操作中因为两列属性不同和无法完成合并操作
            df['date'] = pd.to_datetime(df['date'])
            df_main = pd.concat([df_main, df],sort = False)
            #为了和老版本进行兼容，这里对输出的列做了严格的规划
            #如果改动的话，会对海龟模型中ATR的rawData有所破坏，导致加载失败
            df_main = df_main[['date','code','close','TR','ATR','MAHR_100_HIGH','MAHR_20','MAHR_30','MAHR_100_HIGH_DEV','MAHR_20_DEV','MAHR_30_DEV','MAX_MAHR_20_LOW_DEV','MAX_MAHR_30_LOW_DEV']]
        #保存数据
        if to_csv == True:
            #print(df_main)
            df_main.to_csv('.\\trade\\ATR_jqdata.csv', encoding = 'utf_8_sig')
        return df_main

