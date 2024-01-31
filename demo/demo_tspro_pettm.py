"""
本模块用于展示如何绘制PE/TTM图
主坐标画出close线，副坐标画出pe_ttm线，副图叠加换手率turnover_rate_f的柱状图
"""
import pandas as pd
import numpy as np
import json
import io
import mplfinance as mpf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime,timedelta
from apt.vendor.tspro.data import data as ts_data
from apt.vendor.akshare.data import data as ak_data  
import mplfinance as mpf

# 假设我们有以下数据
ak = ak_data()
ak.code = '600648.sh'
ak.start_date = datetime(2023,1,1)
ak.end_date = datetime(2024,1,20)
sql_str = f"select date,close,turnover_rate_f,pe_ttm from tspro_basic where code='{ak.code}' and date between '{ak.start_date.date()}' and '{ak.end_date.date()}'"
df = pd.read_sql(sql_str,ak.engine)
print(df)

# 获取数据
dates = df['date']
close = df['close']
pe_ttm = df['pe_ttm']
turnover_rate_f = df['turnover_rate_f']

# 创建一个新的图形
fig, ax1 = plt.subplots()

# 绘制close数据
ax1.plot(dates, close, label='Close', color='tab:blue')
ax1.set_xlabel('日期')
ax1.set_ylabel('Close', color='tab:blue')

# 创建一个共享x轴的副坐标轴
ax2 = ax1.twinx()
# 绘制pe_ttm数据
ax2.plot(dates, pe_ttm, label='PE/TTM', color='tab:red')
ax2.set_ylabel('PE/TTM', color='tab:red')

# 创建一个新的副图来绘制换手率的柱状图
ax3 = fig.add_subplot(2, 1, 2)
ax3.bar(dates, turnover_rate_f, label='Turnover Rate')
ax3.set_xlabel('日期')
ax3.set_ylabel('Turnover Rate')

# 设置主图和副图的x轴为日期类型
#ax1.xaxis.set_major_locator(mdates.WeekdayLocator())
#ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
#ax2.xaxis.set_major_locator(mdates.WeekdayLocator())
#ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
#ax3.xaxis.set_major_locator(mdates.WeekdayLocator())
#ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

plt.show()