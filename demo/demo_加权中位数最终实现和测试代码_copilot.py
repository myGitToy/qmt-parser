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
df = pd.DataFrame({'close': [1, 2, 3],
                        'volume': [2, 3, 40]})

#print(df)
#取得区间内的加权平均价格分布
# 按收盘价分组，计算每个价格的总成交量
volume_by_price = df.groupby('close')['volume'].sum()

# 计算累计成交量百分比
volume_by_price = volume_by_price.sort_index()
cumulative_volume_pct = volume_by_price.cumsum() / volume_by_price.sum()

# 找出每5%分位数对应的价格
quantiles = np.round(np.arange(0.05, 1.05, 0.05), 2)
prices_at_quantiles = cumulative_volume_pct.index[cumulative_volume_pct.searchsorted(quantiles)]

# 四舍五入到小数点后两位
prices_at_quantiles = prices_at_quantiles.round(2)
output = pd.Series(prices_at_quantiles, index=quantiles).to_json()
print(output)