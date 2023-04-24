"""
测试背景：对于一些冲高回落的股票，如果单纯从中位数的角度去统计均值，因为成交量不同，因此会产生误差
解决方案就是计算加权价格，去统计对应的中位数或者75%分位数

bing提问：我有一组数据，是股票的成交价格和成交量，现在要计算根据成交量分布的成交价格中位数和75%分位数，用python代码呈现

bing回答：

你好，根据网上的资料123，你可以用numpy或pandas的函数来计算分位数。例如，如果你的数据是一个numpy数组，你可以用percentile函数来计算中位数和75%分位数，如下：

import numpy as np
# 假设data是一个二维数组，第一列是成交价格，第二列是成交量
price = data[:,0] # 取出成交价格
volume = data[:,1] # 取出成交量
# 根据成交量对价格进行加权
weighted_price = np.repeat(price, volume)
# 计算中位数和75%分位数
median = np.percentile(weighted_price, 50)
q75 = np.percentile(weighted_price, 75)
print(median, q75)
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
a.code = '002049.SZ'
a.start_date = datetime(2023,3,23,8,0,0)
a.end_date = datetime(2023,4,21,15,59,0)
a.fq = data.复权.动态复权
a.ktype = '1m'
a.vendor = a.vendor.tusharePro

#获取数据
df = a.get_k_data()
print(df)

#根据GPT给出的代码进行适配
price = df['close'] # 取出成交价格
volume = df['volume'] # 取出成交量
# 根据成交量对价格进行加权
#weighted_price = np.repeat(price, volume)
#print(weighted_price)
# 计算中位数和75%分位数
median = np.percentile(df['close'], 50)
q75 = np.percentile(df['close'], 75)
print(median, q75)

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