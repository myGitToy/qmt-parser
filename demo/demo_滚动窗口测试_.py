"""
测试背景：测试滚动窗口，使用apply和lamda
本模块针对滚动窗口进行测试，使用方法3
"""
import numpy as np
import pandas as pd
from apt.qsp_universal.base import base as data
from datetime import datetime ,timedelta
from demo_quantile import weighted_quantile,weighted_quantile_df
# 列名与数据对其显示
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
# 显示所有行列
#pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 20)
############1. 基础数据参数设置
a = data()
a.code = '300343.SZ'
a.start_date = datetime(2023,4,24,8,0,0)
a.end_date = datetime(2023,4,28,15,59,0)
a.fq = data.复权.动态复权
a.ktype = '1m'
a.vendor = a.vendor.tusharePro
rolling_N = 20
#获取数据
df = a.get_k_data()

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



a = pd.Series([1, 2, 3])
b = pd.Series([2, 3, 40])
print(a)
print(b)
#测试np.repeat
c = np.repeat(a , b )   #测试结果符合预期
print(f"np.repeat方法下，25，50，75分位数分别为{np.percentile(c, 25)}|{np.percentile(c, 50)}|{np.percentile(c, 75)}")
#测试np.stack
c = np.stack((a,b)) #[[1 2 3]
                    # [2 3 4]]

#测试np.concatenate
#c = np.concatenate((a,b))   #简单堆叠，变成[1 2 3 2 3 4]
#c = np.concatenate((a,b) , axis = 1) #错误
print(c)
new_qutile = weighted_quantile_df(values = a ,quantiles = [0.25,0.5,0.75] , sample_weight = b )
#new_qutile = weighted_quantile(values = df['close'] ,quantiles = [0.25,0.5,0.75] , sample_weight = df['volume'] )
print(new_qutile)
print(df['close'].rolling(5))
qt = quantile(data = df['close'], weights = df['volume'], quantile = [0.25,0.5,0.75])
print(qt)
#percentile_75 = np.percentile(a, 75, weights=b)
#print(percentile_75)
#测试apply和lambda方法
df['weighted_close'] = df['close'] * df['volume']

"""
# 计算滚动窗口下的75%分位数收盘(这里的测试结果还是加权平均rolling后取分位数，和我需要的结果并不符合)
# 计算加权平均收盘价
df['weighted_close'] = df['close'] * df['volume']
df['rolling_weighted_close'] = df['weighted_close'].rolling(window=rolling_N).sum()
df['rolling_volume'] = df['volume'].rolling(window=rolling_N).sum()
df['rolling_close'] = df['rolling_weighted_close'] / df['rolling_volume']
df['25_percentile_close'] = df['rolling_close'].rolling(window=rolling_N).quantile(0.25)
# 打印结果
print(df[['date','close','volume','rolling_close','25_percentile_close']])
"""

#滚动窗口测试区间最大最小值
df['min'] = df['open'].rolling(window = rolling_N ).apply(lambda x : np.min(x))
print(df['min'])
print(df)
