import pandas as pd
from apt.qsp_universal.base import base
from datetime import datetime
from mpl_finance import candlestick_ochl
import matplotlib.pyplot as plt
# 显示所有列
#pd.set_option('display.max_columns', None)
#pd.set_option('display.max_rows', None)

tspro = base()
tspro.code ='601318.sh'
tspro.vendor = tspro.vendor.tusharePro
tspro.start_date= datetime(2022,7,5,8)
tspro.end_date = datetime(2022,7,7,16)
tspro.fq = tspro.复权.动态复权
tspro.ktype = '1d'

#ts数据
df_ts = tspro.get_k_data()
df_ts['close'].plot()
# 先画日K线
#fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(20, 8), dpi=80)
#candlestick_ochl(axes, df_ts.values, width=0.2, colorup='r', colordown='g')
#plt.show()
#[['code','date','close','factor']]
#print(df_ts)
#jqdata数据
tspro.code = '603986.XSHG'
tspro.vendor = tspro.vendor.jqdata
df_jqdata = tspro.get_k_data()
#print(df_jqdata)

    
