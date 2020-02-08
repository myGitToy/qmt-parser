# -*- coding: utf-8 -*-
from datetime import datetime,timedelta
import numpy as np
import pandas as pd
import tushare as ts
#定义证券代码列表
code_list = ['510300','510500','159949','512760','512880','512290','512580','512980']
#读取数据
df_main = pd.DataFrame()
for code in code_list:
    df = pd.read_csv('.\\data\\day\\%s.csv' % (code))
    df = df[['date','code','open','close','high','low','volume']]
    print(df)
    df_main = pd.concat([df_main, df],sort = False)
#print(df_main)
pv = pd.pivot_table(df_main, index=['code','date'] , values = ['close','high'] )
pv['MA20'] = pv['close'].rolling(20).mean()
#pv['MA20'] = pv.groupby(['code'])['close'].rolling(20).mean()
pv.to_csv('.\\data\\temp_pivot.csv')
#pv = df_main.pivot(index = ['date','code'] , columns = 'close' )
#数据透析表多条件查询
print('数据透析表多条件查询')
df2 = pv.query('date >= "2020-01-05" & code == 510500')
print(df2)
print('使用groupby 效果一样的')
gp = df_main.groupby(['code','date']).mean()
gp['MA20'] = gp['close'].rolling(20).mean()
#'date','code'不能放在里面，因为groupby 把他们转换成索引了，所以列标签只有close和MA20
print(gp[['close','MA20']])

