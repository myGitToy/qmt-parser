#测试日线数据取得的ATR数据，叠加小时线上的100小时新高次数
#目的是为了测试两种不同日期结构下的数据拼接技术
from datetime import datetime,timedelta
import numpy as np
import pandas as pd
import tushare as ts
import logging
import os
import analyse
from analyse import ATR
from apt.qsp.k import k

a = ATR(code = '000063' , start = '2020-01-01' )
a.network_OK =  True
df = a.cal_ATR()

print(df)