"""
本模块用于测试mysql数据库对于json格式数据的支持
同时用来测试全换手区间的计算
"""
import pandas as pd
import numpy as np
import json
import io
import mplfinance as mpf
import matplotlib.pyplot as plt

from datetime import datetime,timedelta
from apt.vendor.tspro.data import data as ts_data
from apt.vendor.akshare.data import data as ak_data
"""
测试从cumulative_turnover中读取数据，然后计算价格分布
"""
#1. 初始化
a = ak_data()
a.code = '000798.sz'
a.start_date = datetime(2023,1,2,8)
a.end_date = datetime(2023,12,20,18)
a.ktype = '1d'
df = a.get_k_data()
print(df)
#2. 读取全换手数据
sql_str = f"SELECT * FROM stock.tspro_cumulative_turnover WHERE CODE='{a.code}' AND date(date) between '{a.start_date.date()}' and '{a.end_date.date()}'"
df_db = pd.read_sql(sql_str , a.engine)
#显示交易日
show_days = df_db['turnover_days_f'].iloc[-1] + 20
if show_days < df_db.shape[0]:
    #如果总交易日小于数据行数，说明可以进行缩减数据，df_db取最后shows_days行数据
    df_db = df_db.tail(show_days)

    #df_db = df_db.iloc[-show_days:]
print(df_db)

#3. 循环读取数据库中的日期，进行元素级别操作
#df_db['K线数量'] = df_db.apply(__lambda_K线校验 , k_type = '1m' , axis = 1)

#这一表明得到全部的价格分布
#df_db['价格分布'] = df_db.apply(__lambda_价格区间 , k_type = a.ktype , axis = 1)
#得到最last的价格分布
#----画出df的K线（价格走势）----
df['date'] = pd.to_datetime(df['date'])
df.set_index('date', inplace=True)
#mpf.plot(df, type='candle', style='charles', title='K线图', ylabel='价格')

#主图上绘制0.25，0.5，0.75分位数对应的价格
# 创建一个空的DataFrame，索引与df_db相同
print(df_db[['code','date','price_range_1d']])
df_lines = pd.DataFrame(index=df_db.index)
json_string = df_db['price_range_1d'].iloc[-1]
v_line = df_db['turnover_date'].iloc[-1]
# 将JSON字符串转换为字典

data = json.loads(json_string)
print(type(data))
# 添加三条横线  
price1 = data['0.1']
price2 = data['0.25']
price3 = data['0.5']
price4 = data['0.75']
price5 = data['0.9']
# 创建一个与df长度相同的列表，所有元素都是price3
line1 = [price1] * len(df)
line2 = [price2] * len(df)
line3 = [price3] * len(df)
line4 = [price4] * len(df)
line5 = [price5] * len(df)
# 设置matplotlib的字体为支持中文的字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # SimHei是黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题

# 创建一个addplot对象，用于在K线图上添加横线
ap = [mpf.make_addplot(line1 , ylabel = '0.10分位数'),  # 添加第一条线
      mpf.make_addplot(line2 , ylabel = '0.25分位数'),  # 添加第二条线
      mpf.make_addplot(line3 , ylabel = '0.50分位数'),  # 添加第三条线
      mpf.make_addplot(line4 , ylabel = '0.75分位数'),  # 添加第四条线
      mpf.make_addplot(line5 , ylabel = '0.90分位数')]  # 添加第五条线


# 绘制K线图，并添加横线
mpf.plot(df, type='candle', style='charles', title='K线图', ylabel='价格' ,addplot=ap ,vlines=dict(vlines=[v_line], linewidths=(1)))


"""
#----绘制df_db最后一组成交价格分布图----

json_string = df_db['价格分布'].iloc[-1]
# 将JSON数据转换为DataFrame
df_json = pd.read_json(io.StringIO(json_string), orient='index')
print(df_json.columns)
# 创建一个空的DataFrame，索引与df_db相同
df_lines = pd.DataFrame(index=df_db.index)
# 对于df_json中的每一行，添加一条横线
for _, row in df_json.iterrows():
    df_lines[row['quantile']] = row['price']
# 创建一个addplot对象，用于在K线图上添加横线
ap = [mpf.make_addplot(df_lines[col]) for col in df_lines.columns]
# 绘制K线图，并添加横线
mpf.plot(df_db, type='candle', style='charles', title='K线图', ylabel='价格', addplot=ap)


# 在同一图形上绘制成交价格的分布图
#plt.bar(df_json.index, df_json[0])
#plt.show()
"""




