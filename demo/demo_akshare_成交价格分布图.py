import pandas as pd
import akshare as ak
import matplotlib.pyplot as plt
import mplfinance as mpf
from datetime import datetime
from apt.vendor.akshare.data import data

# 假设你的 DataFrame 是 df，'price' 列是成交价格
stock = data()
stock.code = '600448.sh'
stock.ktype = '1d'
stock.start_date = datetime(2024,1,1)
stock.end_date = datetime(2024,1,29)
df = stock.get_k_data()
print(df)
# 将 df 的索引转换为 DatetimeIndex
df.index = pd.to_datetime(df.index)
# 假设 df 是一个包含 'open', 'high', 'low', 'close' 和 'volume' 列的 DataFrame
# 'open', 'high', 'low', 'close' 列是每日开盘价、最高价、最低价和收盘价，'volume' 列是每日成交量

# 计算每个价格级别的总成交量
chip_distribution = df.groupby('close')['volume'].sum()

# 创建一个新的 figure 对象和两个 subplot
fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(10, 8))

# 在第一个 subplot 上绘制筹码分布
ax1.bar(chip_distribution.index, chip_distribution.values, color='blue')
ax1.set_ylabel('Volume')

# 在第二个 subplot 上绘制 K线图和成交量
mpf.plot(df, type='candle', volume=True, ax=ax2, mav=(5,10))

plt.show()