# -*- coding: utf-8 -*-
from  apt.os.data_load import Data_Load as dl
"""
【K线选股系统】


"""
class k:
    def __init__(self):
        pass
    def k_new_high_count(self , code : str , start = None , end = None , ktype = "D" , MA_HIGH_PERIOD = 100):
        """
        【计算K线中指定周期新高的次数】
        常规使用小时线上100小时新高（ktype = 60 , MA_HIGH_PERIOD = 100）
        code start end ktype均为常规参数
        MA_HIGH_PERIOD：计算新高的周期，需要和ktype配合使用
        【注意】数据前MA_HIGH_PERIOD中新高数据均为NA，因rolling前滚取不到数据的缘故
        """
        df = dl.load_data(self , code = code , start = start , end = end , ktype = ktype)
        #小时线100小时最高收盘价计算
        df['MAHR_100_HIGH'] = df['high'].rolling(MA_HIGH_PERIOD).max()
        #计算此时点的最高是否为新高
        df.loc[df.MAHR_100_HIGH == df.high,'new_high'] = 1    
        #累计回滚新高
        df = df.fillna(0)
        df['new_high_count'] = df['new_high'].rolling(MA_HIGH_PERIOD).sum()
        #if df['MAHR_100_HIGH'] == df.copy()['high']:
        #    df['new_high_count'] = 1
        return df

