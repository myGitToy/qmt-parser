from datetime import datetime 
import numpy as np
import tushare as ts
import pandas as pd
import matplotlib.pyplot as plt
from apt.qsp_universal.base import base as data
# 列名与数据对其显示
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
# 显示所有列
#pd.set_option('display.max_columns', None)
a = data()
a.code = '002714.sz'
a.start_date = datetime(2022,7,8,4)
a.end_date = datetime(2022,7,8,16)
a.fq = data.复权.动态复权
a.ktype = '1m'
a.vendor = a.vendor.tusharePro
df = a.get_k_data().sort_values(by = ['date'] )
df['close_diff'] = df['close'] - df['close'].shift(1)
#np.where单独使用，符合条件的返回array组，再使用iloc进行定位和修订
df['money_flow'] = np.nan
#df.iloc[np.where(df['close_diff'] > 0)]['money_flow'] = 1
#
df['money_flow'] = np.where(df['close_diff'] > 0 , df['money'] , df['money_flow'] )
df['money_flow'] = np.where(df['close_diff'] < 0 , -df['money'] , df['money_flow'] )
df['money_flow'] = np.where(df['close_diff'] == 0 , 0 , df['money_flow'] )
df['cumsum'] = df['money_flow'].cumsum()

df.set_index('date',inplace=True)
#print(df[['date','close','close_diff','money','money_flow','cumsum']])
#统一各股资金流向的坐标轴，统一按照1个million来计算，也就是对应的1e7
df['cumsum'] = df['cumsum'] / 1000000
df[['cumsum','close']].plot()
#设置标题
plt.rcParams['font.sans-serif']=['SimHei'] #用来正常显示中文
plt.rcParams['axes.unicode_minus']=False #用来正常显示负号
plt.xlabel('时间')
plt.ylabel('资金流向（百万元人民币）')
plt.title(f'{a.code}:{a.start_date.date()}-{a.end_date.date()}资金流向表' )
plt.show()


df['amount'] = np.where(df['close_diff'] < 0 , df['money'] , 0)
#df['amount'] = np.where(df['close_diff'] == 0 , 0 , 0)
print(df[['date','close','close_diff','money','money_flow']])
#通过一分钟线的高低进行资金流向的分析

df['trade_time'] = pd.to_datetime(df['trade_time'])
df.set_index('trade_time',inplace = True)
print(df)
#提取分位数数据
np75 = np.percentile(df['close'],75)
print(np75)
np25 = np.percentile(df['close'],25)
print(np25)
d2 = df.query("close >= @np25 and close <= @np75")
#.query('factor_date <= @self.start_date').iloc[-1].at['factor']
print(d2)
#合成日线
print('合成的日线数据')
dfday = d2.resample('D').agg({'open':'first',
							   'high':'max',
							   'low':'min',
							   'close':'last',
							   'vol':'sum',
							   'amount':'sum'})
print(dfday)
print('原始的日线数据')
df_day = ts.pro_bar(api = a.api  , ts_code = a.code, freq = 'D' ,start_date = a.start_date.strftime('%Y%m%d') , end_date = a.end_date.strftime('%Y%m%d'))
print(df_day)

		