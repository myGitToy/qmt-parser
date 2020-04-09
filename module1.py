from datetime import datetime,timedelta
import numpy as np
import pandas as pd
import tushare as ts
import logging
import os
#显示所有列
pd.set_option('display.max_columns', None)

df=ts.get_k_data('000651', ktype='15')
print(df)
#df.to_csv(('.\\data\\temp.csv')
