"""
测试背景：对于一些冲高回落的股票，如果单纯从中位数的角度去统计均值，因为成交量不同，因此会产生误差
解决方案就是计算加权价格，去统计对应的中位数或者75%分位数


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
#pd.set_option('display.max_rows', None)
############1. 基础数据参数设置
a = data()
a.code = '605389.SH'
a.start_date = datetime(2024,1,10,8)
a.end_date = datetime(2024,1,18,16)
a.fq = data.复权.动态复权
a.ktype = '1m'
a.vendor = a.vendor.akshare

#获取数据
df = a.get_k_data()
print(df)

#校验数据 start_date那天必须要有数据
if df.loc[df['date'].dt.date == a.start_date.date()].empty:
    print("start_date那天没有数据，请重新设置start_date")
    exit()

#根据GPT给出的代码进行适配
price = df['close'] # 取出成交价格
volume = df['volume'] # 取出成交量
# 根据成交量对价格进行加权
#weighted_price = np.repeat(price, volume)
#print(weighted_price)
########方法1（算数平均值）：计算中位数和75%分位数
m_p50 = np.percentile(df['close'], 50)
m_p75 = np.percentile(df['close'], 75)
print(f"算数平均值：中位数{m_p50}|75分位数数{m_p75}")

########方法2（加权平均值）：计算中位数和75%分位数
#此方法最大的问题是运算速度极慢，且内存占用大
# 根据成交量对价格进行加权
#weighted_price = np.repeat(price, volume)
# 计算中位数和75%分位数
#w_p50 = np.percentile(weighted_price, 50)
#w_p75 = np.percentile(weighted_price, 75)
#print(f"加权平均值（慢速版）：中位数{w_p50}|75分位数数{w_p75}")


########方法3（加权平均值 z-score方法）：计算中位数和75%分位数
"""
#目的：增加方法2的运行速度以及内存占用
# 根据成交量对价格进行加权
#使用z-score滚动计算加权成交量需要注意的地方
1. 采用1分钟线：开盘和收盘的集合竞价会产生大量的成交量，以及收盘前最后2分钟成交量为0，这会导致min也为0，对真实的计算会产生比较大的干扰
2. 采用60分钟线，如果选用较短周期，比如N = 4 因为会跨开盘和收盘的数据，实际成交量相同的情况下，z-score分数也会相差比较大，因此需要调整周期，要选用相对比较长的周期，比如N = 4 * 10
"""
#z-score均一
min = df['volume'].min()
max = df['volume'].max()
df['score'] = (df['volume'] - min)/(max - min)
score = df['score']*100   #正常情况下*1000精度已经满足要求，保守处理可以*10000
print(score)
score_price = np.repeat(price, score)
print(score_price)
#print(score_price.where(score_price = 8.04))
# 计算中位数和75%分位数
s_p50 = np.percentile(score_price, 50)
s_p75 = np.percentile(score_price, 75)
print(f"加权平均值（z-score）：中位数{s_p50}|75分位数数{s_p75}")

########方法4（VWAP法）：目前根据原理，只能计算N周期的加权移动平均成交线
# 假设你的数据框名为df，其中包含日期、收盘价和成交量列
df['VWAP'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
df['VWAP_20d'] = df['VWAP'].rolling(240).mean()
df['75%_VWAP_20d'] = df['VWAP_20d'].rolling(240).quantile(0.75)
print(df[['date','close','VWAP','VWAP_20d','75%_VWAP_20d']])


"""
# 对加权后的价格进行排序(速度加快版)
sorted_price = np.sort(weighted_price)
# 计算中位数和75%分位数的位置
n = len(sorted_price)
p50 = 0.5 * (n - 1)
p75 = 0.75 * (n - 1)
# 用np.searchsorted函数找到位置的左右边界
left50 = np.searchsorted(sorted_price, sorted_price[int(p50)], side='left')
right50 = np.searchsorted(sorted_price, sorted_price[int(p50)], side='right')
left75 = np.searchsorted(sorted_price, sorted_price[int(p75)], side='left')
right75 = np.searchsorted(sorted_price, sorted_price[int(p75)], side='right')
# 用插值法计算分位数的值
median = sorted_price[int(p50)] + (p50 - int(p50)) * (sorted_price[right50] - sorted_price[left50])
q75 = sorted_price[int(p75)] + (p75 - int(p75)) * (sorted_price[right75] - sorted_price[left75])
print(median, q75)
"""