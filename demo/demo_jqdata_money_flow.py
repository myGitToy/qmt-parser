from jqdatasdk import *
import pandas as pd
import datetime
import sqlalchemy
from apt.vendor.jqdata.jqdata import jqdata as jqdata
from apt.vendor.jqdata.ETF import ETF as ETF

#显示所有列
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
auth('13817092632','JQ@tushare123')

start = datetime.datetime(2020,12,8)
end = datetime.datetime(2020,12,9)
print(start)
print(start.date())
code = '511220.XSHG'

#获取全部
#df = get_money_flow(['300142.XSHE'], start_date='2020-6-16', end_date='2020-9-16', fields=None, count=None)
#获取大单date     sec_code  change_pct  net_amount_main  net_pct_main
df = get_money_flow(['002647.XSHE'] , start_date = start, end_date = end , fields = ['date','change_pct','net_amount_main','net_pct_main'] , count = None)
df['net_pct_main_ma']=df['net_pct_main'].rolling(5).mean()
print(df)




