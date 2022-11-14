import numpy as np
import tushare as ts
import pandas as pd
import matplotlib.pyplot as plt
from apt.qsp_universal.base import base as data
from apt.vendor.tspro.data import data as tspro
from datetime import datetime,timedelta
# 列名与数据对其显示
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
# 显示所有列
#pd.set_option('display.max_columns', None)
a = data()
a.code = '512760.sh'
a.start_date = tspro.start_date = datetime(2022,1,1,4)
a.end_date = tspro.end_date = datetime(2022,7,15,16)
a.fq = data.复权.动态复权
a.ktype = '1d'
a.vendor = a.vendor.tusharePro
pro = ts.pro_api('55297f16c0119146589e059db315ba28a9412e89ec9f91e538e655b2')
#基金份额数据获取
share =  pro.fund_share(ts_code = a.code , start_date = tspro.start_date.strftime('%Y%m%d') , end_date = tspro.end_date.strftime('%Y%m%d'))
#格式处理
share.rename(columns={"trade_date": "date"} , errors="raise" , inplace = True)
share['date'] = pd.to_datetime(share['date'] )
share.sort_values(by = 'date' , ascending = True , inplace = True)

#基金收盘价数据获取
df = a.get_k_data().sort_values(by = ['date'] )
# 格式处理
df['date'] = pd.to_datetime(df['date'])

#数据拼接
df = pd.merge(df, share[['date','fd_share']] , on = ['date'] , how = 'left')
print(df)
df.set_index('date',inplace = True)
#print(df[['date','close','close_diff','money','money_flow','cumsum']])
#统一各股资金流向的坐标轴，统一按照1个million来计算，也就是对应的1e7
plt.rcParams['font.sans-serif']=['SimHei'] #用来正常显示中文
plt.rcParams['axes.unicode_minus']=False #用来正常显示负号
fig, ax1 = plt.subplots()
ax2 = ax1.twinx()    # mirror the ax1
# 使用xticks
# 这句是核心
plt.xticks(range(0,len(df.index),90),list(df.index)[::90], rotation = 90)
#把X轴的时间进行转换，用来解决时间点断续的问题
ax1.plot(range(len(df.index)), df['close'], 'g-')
ax2.plot(range(len(df.index)), df['fd_share'], 'b-')
ax1.set_xlabel('时间')
ax1.set_ylabel('收盘价', color='g')
ax2.set_ylabel('基金份额（百万元人民币）', color='b')
plt.title(f'{a.code}:{a.start_date.date()}-{a.end_date.date()}资金流向表' )
plt.show()

