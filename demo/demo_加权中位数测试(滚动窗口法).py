"""
测试背景：加权中位数的问题计算方法已经解决，实际落地过程中需要对连续N天的数据进行计算，因此需要用到滚动窗口的概念
本模块针对滚动窗口进行测试，使用方法3
"""
import numpy as np
import pandas as pd
from apt.qsp_universal.base import base as data
from datetime import datetime ,timedelta

# 列名与数据对其显示
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
# 显示所有行列
#pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 20)
############1. 基础数据参数设置
a = data()
a.code = '300343.SZ'
a.start_date = datetime(2023,4,13,8,0,0)
a.end_date = datetime(2023,4,28,15,59,0)
a.fq = data.复权.动态复权
a.ktype = '60m'
a.vendor = a.vendor.tusharePro
rolling_N = 4
#获取数据
df = a.get_k_data()
print(df)

#bing测试
def percentile_zscore(df):
    print(df)
    price = df['close'] # 取出成交价格
    min = df['volume'].min()
    max = df['volume'].max()
    df['score'] = (df['volume'] - min)/(max - min)
    score = df['score']*10000   #正常情况下*1000精度已经满足要求，保守处理可以*10000
    print(score)
    score_price = np.repeat(price, score)
    # 计算中位数和75%分位数
    s_p50 = np.percentile(score_price, 50)
    s_p75 = np.percentile(score_price, 75)
    print(f"加权平均值（z-score）：中位数{s_p50}|75分位数数{s_p75}")
    return s_p50 , s_p75

# 计算10天动态滚动窗口的加权中位数价格
#rolling_window = df['close'].rolling(window=10800)
#weighted_median = rolling_window.apply(lambda x: np.average(x, weights=df.loc[x.index]['volume']))
#z_score = rolling_window.apply(lambda x: (x[-1] - np.mean(x)) / np.std(x))
#weighted_75th_percentile = rolling_window.apply(lambda x: np.percentile(x, q=75, weights=df.loc[x.index]['volume']))
#print(weighted_75th_percentile)


#根据GPT给出的代码进行适配
price = df['close'] # 取出成交价格
volume = df['volume'] # 取出成交量
# 根据成交量对价格进行加权
#weighted_price = np.repeat(price, volume)
#print(weighted_price)

#测试用函数实现
#result = df.rolling(40 , method = 'table').apply(lambda x: percentile_zscore(x), raw = True , engine = 'numba')
#[['close','volume']]
#result = df.rolling(40 , method = 'table').apply(percentile_zscore , raw = True , engine = 'numba')
#print(result)

########方法3（加权平均值 z-score方法）：计算中位数和75%分位数
#目的：增加方法2的运行速度以及内存占用
# 根据成交量对价格进行加权
#z-score均一

df['rolling_min'] = df['volume'].rolling(rolling_N).min()
df['rolling_max'] = df['volume'].rolling(rolling_N).max()
print(df)
#df['weighted_price'] = np.repeat(df['close'], df['volume'])
#print(f"当日最高成交价：{min}；当日最低成交价{max}")
df['v_score'] = (df['volume'] - df['rolling_min'])/(df['rolling_max'] - df['rolling_min'])

#z-score 精度处理及置零（置零会在后续处理中发生问题，权重处理时全为0的情况下会报错，因此此处进行dropna处理）
#正常情况下*1000精度已经满足要求，保守处理可以*10000
df['v_score'].dropna( inplace = True)
df['v_score'].fillna(1 , inplace = True)
df['v_score'] = df['v_score'] * 1000
print(df[['date','close','v_score']])
#test np.repeat
weight_close = np.repeat(df['close'],df['v_score'])
print(weight_close)
print(f"加权平均值：75分位数{np.percentile(weight_close, 75)}|中位数{np.percentile(weight_close, 50)}|25分位数数{np.percentile(weight_close, 25)}")
print(df[['date','close','rolling_min','rolling_max','v_score']].tail(2000))
#df.loc[df['v_score'] ==  np.NaN, 'v_score'] = 0
#df['v_score'] = np.where(df['v_score'] == np.nan , 0 , df['v_score'] * 10000)
#print(df)
#print(df.query("v_score <=0"))
#To set negative values in a pandas dataframe to zero

#df['v_score'] = df['v_score'] * 10000   
#print(score)
df['w_75'] = df.rolling(window=10).apply(percentile_75)

df['w_50'] = df['close'].rolling(rolling_N).apply(lambda x: np.average(x, weights=df.loc[x.index]['v_score']))
df['w_75'] = df['close'].rolling(rolling_N).apply(lambda x: np.percentile(x, q = 75, weights=df.loc[x.index]['v_score']))
#df['v_price'] = np.repeat(df['close'].rolling(240). , df['v_score'].rolling(240))
# 计算中位数和75%分位数
#df['w_p50'] = np.percentile(v_price, 50)
#df['w_p75'] = np.percentile(v_price, 75)
print(df)
#print(f"加权平均值：中位数{s_p50}|75分位数数{s_p75}")

