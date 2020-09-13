#测试均线的斜率
#测试认为3日斜率 ma3_slope>0.0005 即5e-4 可以认为斜率为正

from datetime import datetime,timedelta
import numpy as np
import pandas as pd
import tushare as ts
import logging
import os
import analyse
from analyse import ATR
#from apt.qsp.k import k
from  apt.os.data_load import Data_Load 

def get_line_k(code = None , start = None , end = None , ktype = 60 , MA = 30):
    df = dl.load_data(self ,  code = code , start = start , end = end , ktype = ktype)
    df['diff_percent'] = (df['close'] - df['close'].shift(1)) / df['close']
if __name__=="__main__":
    __code = '512880'
    __start =  '2020-05-01'
    __end =  '2020-09-09'
    __ktype = 60
    __MA = 30
    dl = Data_Load()
    df = dl.load_data(code = __code , start = __start , end = __end , ktype = __ktype)
    #小时线30小时均线价格
    df['ma'] = df['close'].rolling(__MA).mean()
    df['ma_slope'] = (df['ma'] - df['ma'].shift(1)) / df['ma']
    df['ma3_slope'] = df['ma_slope'].rolling(3).mean()
    #df = get_line_k(self , code = __code ,  start = __start , end = __end , ktype = __ktype)
    print(df)

