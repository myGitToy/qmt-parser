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
def __lambda_价格区间(row , k_type = '1m'):
    """
    全换手区间价格分布 每0.05为一个分位数
    【输入】
        row：数据行（tspro_cumulative_turnover） 必须包含的列：code,date,turnover_date
        k_type：K线类型 默认为1m  
    【返回】
        JSON值 分位数分布
    """
    ak = ak_data()
    ak.code = row['code']
    ak.start_date = pd.to_datetime(row['turnover_date']) + timedelta(hours=8)
    ak.end_date = pd.to_datetime(row['date']) + timedelta(hours=16)
    ak.ktype = k_type
    df = ak.get_k_data()
    if df.empty:
        raise ValueError('没有数据')
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
    # 输出JSON
    output = pd.Series(prices_at_quantiles, index=quantiles).to_json()
    print(f'code:{ak.code} date:{ak.end_date} 价格区间：')
    print(output)
    #显示json元素的名称
    print('-------------------') 
    return output

def __lambda_K线校验(row, k_type = '1m'):
    """
    对cumulative_turnover数据进行K线校验，返回区间内的K线数量
    【输入】
        row：数据行 必须包含的列：code,start_date,end_date
        k_type：K线类型 默认为1m
    """
    ak = ak_data()
    ak.code = row['code']
    #这边对开始时间和结束时间进行校验，取日期+8小时/日期+16小时
    #备注：按照cumulative_turnover的数据，开始时间结束时间都是日期类函数，理论上不需要进行校验，这边还是进行校验
    ak.start_date = pd.to_datetime(row['turnover_date']).date() + timedelta(hours=8)
    ak.end_date = pd.to_datetime(row['date']) + timedelta(hours=18)
    ak.ktype = k_type
    df = ak.get_k_data()
    return df.shape[0]  #返回K线数量（这里没有按日期进行汇总，是区间内的总K线数）

#1. 初始化
a = ak_data()
a.code = '603099.sh'
a.start_date = datetime(2023,12,20,8)
a.end_date = datetime(2024,1,23,18)
a.ktype = '1d'
df = a.get_k_data()
print(df)
#2. 读取全换手数据
sql_str = f"SELECT * FROM stock.tspro_cumulative_turnover WHERE CODE='{a.code}' AND date(date) between '{a.start_date.date()}' and '{a.end_date.date()}'"
df_db = pd.read_sql(sql_str , a.engine)
print(df_db)

#3. 循环读取数据库中的日期，进行元素级别操作
#df_db['K线数量'] = df_db.apply(__lambda_K线校验 , k_type = '1m' , axis = 1)

#这一表明得到全部的价格分布
#df_db['价格分布'] = df_db.apply(__lambda_价格区间 , k_type = a.ktype , axis = 1)
#得到最last的价格分布
df_db['价格分布'] = __lambda_价格区间(df_db.iloc[-1] ,k_type = a.ktype )
#----画出df的K线（价格走势）----
df['date'] = pd.to_datetime(df['date'])
df.set_index('date', inplace=True)
#mpf.plot(df, type='candle', style='charles', title='K线图', ylabel='价格')

#主图上绘制0.25，0.5，0.75分位数对应的价格
# 创建一个空的DataFrame，索引与df_db相同
df_lines = pd.DataFrame(index=df_db.index)
json_string = df_db['价格分布'].iloc[-1]
v_line = df_db['turnover_date'].iloc[-1]
# 将JSON字符串转换为字典
data = json.loads(json_string)
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




