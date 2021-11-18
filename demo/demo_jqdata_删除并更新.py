"""
本示例模块演示了jqdata数据出错后，如何删除错误的数据并重新更新写入数据库
注意事项：由于datetime的特性，所以要更新2021/11/18日的数据时，end_date要写成datetime(2021,11,18,16)
"""
from apt.qsp_jqdata.A import A as A
from apt.vendor.jqdata.jqdata import data as data
from datetime import datetime
import pandas as pd
import tushare as ts
import talib as ta

jq = data()
jq.re_update(code = '512170.XSHG' , start_date = datetime(2021,11,16) , end_date = datetime(2021,11,18,16))
