#获取每日净值数据
from jqdatasdk import *
import pandas as pd
import datetime
import sqlalchemy
from apt.vendor.jqdata.jqdata import data as jqdata
from apt.vendor.jqdata.ETF import ETF as ETF

#显示所有列
#pd.set_option('display.max_columns', None)
#pd.set_option('display.max_rows', None)
auth('13817092632','JQ@tushare123')
day = datetime.datetime(2020,12,4)
code = '159949.XSHE'

df = get_fundamentals(query(valuation),day)
print(df)