from datetime import datetime 
import numpy as np
import tushare as ts
import pandas as pd
import matplotlib.pyplot as plt
import mpl_finance as mpf  # 替换 import matplotlib.finance as mpf
from apt.qsp_universal.base import base as data
# 列名与数据对其显示
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
# 显示所有列
#pd.set_option('display.max_columns', None)
a = data()
a.code = '002466.sz'
a.start_date = datetime(2022,7,20,4)
a.end_date = datetime(2022,7,22,16)
a.fq = data.复权.动态复权
a.ktype = '1m'
a.vendor = a.vendor.tusharePro
name = a.get_security(code = a.code)[0].iloc[0].at['name']    #获取证券名称
df = a.get_k_data().sort_values(by = ['date'] )
#删除9:30和15:00的数据
df = df.query('date.dt.time != datetime.strptime("09:30","%H:%M").time()')
df = df.query('date.dt.time != datetime.strptime("15:00","%H:%M").time()')
df['close_diff'] = df['close'] - df['close'].shift(1)
#np.where单独使用，符合条件的返回array组，再使用iloc进行定位和修订
df['money_flow'] = np.nan
#df.iloc[np.where(df['close_diff'] > 0)]['money_flow'] = 1
df['money_flow'] = np.where(df['close_diff'] > 0 , df['money'] , df['money_flow'] )
df['money_flow'] = np.where(df['close_diff'] < 0 , -df['money'] , df['money_flow'] )
df['money_flow'] = np.where(df['close_diff'] == 0 , 0 , df['money_flow'] )
df['cumsum'] = df['money_flow'].cumsum()
# 对时间进行一下处理
df['date'] = pd.to_datetime(df['date'],format = "%m-%d")
df.set_index('date',inplace=True)
#print(df[['date','close','close_diff','money','money_flow','cumsum']])
#统一各股资金流向的坐标轴，统一按照1个million来计算，也就是对应的1e7
df['cumsum'] = df['cumsum'] / 1000000
plt.rcParams['font.sans-serif']=['SimHei'] #用来正常显示中文
plt.rcParams['axes.unicode_minus']=False #用来正常显示负号
fig, ax1 = plt.subplots()
ax2 = ax1.twinx()    # mirror the ax1
# 使用xticks
# 这句是核心
plt.xticks(range(0,len(df.index),100),list(df.index)[::100], rotation = 90)

# 创建子图
#graph_KAV = fig.add_subplot(1, 1, 1)
mpf.candlestick2_ochl(ax1, df.open, df.close, df.high, df.low, width=0.5,colorup='r', colordown='g')  # 绘制K线走势
plt.gcf().autofmt_xdate()  # 自动旋转日期标记

#把X轴的时间进行转换，用来解决时间点断续的问题
#ax1.plot(range(len(df.index)), df['close'], 'g-')
ax2.plot(range(len(df.index)), df['cumsum'], 'b-')
ax1.set_xlabel('时间')
ax1.set_ylabel('价格', color='g')
ax2.set_ylabel('资金流向（百万元人民币）', color='b')
plt.title(f'{a.code}[{name}]:{a.start_date.date()}-{a.end_date.date()}资金流向表' )
plt.show()

