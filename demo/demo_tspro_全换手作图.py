"""
本模块用于展示如何使用全换手区间的概念来绘制不同分位数下的K线图
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
#------------默认参数设置----------------
tspro = ts_data()
tspro.code ='603516.sh'
tspro.start_date= datetime(2022,4,1,8)
tspro.end_date = datetime(2024,2,20,16) #这里有一个bug，最后一个日期必须完成全换手区间的计算
tspro.fq = tspro.复权.动态复权
tspro.ktype = '1d'
day_plus = 60  #全换手多计算的天数 默认20
#设置默认输出的分位数列
col_p = {"0.15": 'p15',"0.25": 'p25', "0.5": 'p50', "0.75": 'p75' , "0.85": 'p85'}
f_share = True #是否进行全换手计算
#tspro.update_cumulative_turnover()
df_db = tspro.get_p_data(f_share=f_share , col_p = col_p)
print(df_db)
#df中包含正常的OHLC数据，以及cumulative_turnover的数据
#绘制K线图，主图上绘制0.25，0.5，0.75分位数对应的价格曲线
#显示全换手的交易日，默认按照全换手+20天来显示K线图

#------------细节调整------------
if f_share:
    show_days = df_db['turnover_days_f'].iloc[-1] + day_plus  #全流通100%换手所需交易日的调整
else:
    show_days = df_db['turnover_days'].iloc[-1] + day_plus    #总股本100%换手所需交易日的调整
if show_days < df_db.shape[0]:
    #如果总交易日小于数据行数，说明可以进行缩减数据，df_db取最后shows_days行数据
    df_db = df_db.tail(show_days)
else:
    #如果总交易日大于数据行数，说明不能进行缩减数据，直接报错
    raise ValueError('全换手对应的交易日大于数据行数，无法进行作图')

#------------画出主K线（价格走势）------------
#设置索引和X轴坐标
df_db['date'] = pd.to_datetime(df_db['date'])
df_db.set_index('date', inplace=True)
# 创建一个自定义的颜色方案
mc = mpf.make_marketcolors(up='r', down='g', inherit=True)
# 创建一个自定义的样式对象
s = mpf.make_mpf_style(marketcolors=mc)
#mpf.plot(df_db, type='candle', style= s, title='K线图', ylabel='价格' )

#------------画出叠加数据（分位数）------------
#添加垂直线，表明最后一个交易日对应的全换手日期
if f_share:    
    df_db['turnover_date_f'] = pd.to_datetime(df_db['turnover_date_f'])
    v_line = df_db['turnover_date_f'].iloc[-1]
else:
    df_db['turnover_date'] = pd.to_datetime(df_db['turnover_date'])
    v_line = df_db['turnover_date'].iloc[-1]
# 将v_line转换为日期数字
#v_line = pd.to_datetime(v_line)
#v_line = mdates.date2num(v_line)    
#主图上绘制0.25，0.5，0.75分位数对应的价格
# 创建一个空的DataFrame，索引与df_db相同
"""
df_p_data = pd.DataFrame(index=df_db.index)
#从col_p中取出分位数对应的列名
col_p = list(col_p.values())
#加所有列添加到df_lines中
for col in col_p:
    df_p_data[col] = df_db[col]

print(df_p_data['p25'])\
"""
# 创建一个空的addplot列表
addplots = []
# 遍历col_p字典
for percentile, column_name in col_p.items():
    # 从数据框中获取数据
    data = df_db[column_name]
    #将data数据强制转换成数字
    data = pd.to_numeric(data, errors='coerce')
    # 创建一个addplot对象，并添加到列表中
    addplots.append(mpf.make_addplot(data))

# 将addplot列表传递给`addplot`参数
mpf.plot(df_db, type='candle', style=s, title='K线图', ylabel='价格', addplot=addplots ,vlines=dict(vlines=[v_line], linewidths=(1)) , volume = True)
plt.show()
#mpf.plot(df_db, type='candle', style= s, title='K线图', ylabel='价格' , addplot=df_p_data ,vlines=dict(vlines=[v_line], linewidths=(1)))
