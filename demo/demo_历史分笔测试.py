import tushare as ts
import pandas as pd

#df = ts.get_tick_data('159949',date='2020-11-06',src='tt')
df = ts.get_today_ticks(code = '159949')
print(df.tail(50))