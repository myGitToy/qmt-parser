from datetime import datetime,timedelta
import numpy as np
import pandas as pd
import tushare as ts
import logging
import os
from MyTSOS import Data_Load

#显示所有列
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows',   None)
tb = Data_Load()
df = tb.load_data('000651',ktype=5,start='2020/1/1')
print(df)
#时间重采样
re = df.resample('30min').sum()
re.dropna(inplace = True)
print(re)
#df.to_csv(('.\\data\\temp.csv')
