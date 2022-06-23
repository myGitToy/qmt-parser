from datetime import datetime 
import numpy as np
import tushare as ts
import pandas as pd
from apt.vendor.tspro.data import data as data
# 列名与数据对其显示
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
# 显示所有列
pd.set_option('display.max_columns', None)
a = data(myauth = True)
#a.myauth = False
a.code = '600038.sh'
a.start_date = datetime(2022,6,14)
print(a.myauth)
a.end_date = datetime.now()
a.fq = data.复权.不复权
#df = a.pro.trade_cal(exchange='SZSE', start_date='20180101', end_date='20181231')
df = ts.pro_bar(api = a.api , ts_code = a.code, freq = '1min' ,start_date = a.start_date.strftime('%Y%m%d') , end_date = a.end_date.strftime('%Y%m%d'))
#df['close'].astype(np.float)
#df['high'].astype(np.float)
#df['low'].astype(np.float)
#df['open'].astype(np.float)
#df['vol'].astype(np.float)
#df['amount'].astype(np.float)
#设置index
#更改事件烈性
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

		