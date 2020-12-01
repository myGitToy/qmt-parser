#测试日线数据取得的ATR数据，叠加小时线上的100小时新高次数
#目的是为了测试两种不同日期结构下的数据拼接技术
from datetime import datetime,timedelta
import numpy as np
import pandas as pd
import tushare as ts
import logging
import os
import analyse
from analyse import ATR
from apt.qsp.k import k

if __name__=="__main__":
    __code = '510300'
    __start =  '2020-01-01'
    __end =  '2020-09-04'
    a = ATR(code = __code , start = __start , end = __end , ktype = 'D')
    a.network_OK = True
    df_day = a.cal_ATR()
    #交易日期时间序列化
    df_day['date'] = pd.to_datetime( df_day['date'] , format = '%Y-%m-%d' ) 
    print(df_day.tail(5))
    k = k()
    df = k.k_new_high_count(  code = __code , start = __start , end = __end , ktype = 60 )
    #时间序列
    df = df[[ 'new_high_count']]
    #时间重采样（按1天），抛弃无交易日数据和开头因为rolling产生的NA
    df_new_high = df.resample('1D').max().dropna()
    #不加载code则不需要进行处理，其实处理了也没用 510300 处理完毕还是510300.0 因为时间重采样的缘故
    #df_new_high['code'] = df_new_high['code'].astype(np.str)
    print(df_new_high.tail(5))
    # ATR信息与新高次数数据vlookup
    df2 = pd.merge(df_day , df_new_high , on = ['date'], how = 'left')  
    #df2 = df_day.combine_first(df_new_high)
    #输出结果为日线级别的4个基本价格，ATR基础数据，新高次数
    print(df2.tail(5))
