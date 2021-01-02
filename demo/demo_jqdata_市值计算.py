from jqdatasdk import *
import pandas as pd
import datetime
import sqlalchemy
from apt.vendor.jqdata.jqdata import data as jqdata
from apt.vendor.jqdata.ETF import ETF as ETF

#显示所有列
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
auth('13817092632','JQ@tushare123')

start = datetime.datetime(2020,10,12)
end = datetime.datetime(2020,12,22)
#获取市值数据
#q = query(valuation).filter(valuation.code == '000001.XSHE')
q = query(indicator).filter(valuation.code == '000001.XSHE')
#获取多日数据
df = get_fundamentals_continuously(q, end_date = end , count = 20 , panel=False)
#获取当日数据
#df = get_fundamentals(q, '2020-12-25')
print(df)


