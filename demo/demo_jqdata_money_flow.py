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

start = datetime.datetime(2019,1,1)
end = datetime.datetime(2020,12,31)
print(start)
print(start.date())
code = '300869.XSHE'
#df_share = finance.run_query(query(finance.FUND_SHARE_DAILY).filter(finance.FUND_SHARE_DAILY.date >= '2020/12/8' , finance.FUND_SHARE_DAILY.date <= '2020/12/10' , finance.FUND_SHARE_DAILY.code == '159949.XSHE' ))
#print(df_share)
#获取全部
#df = get_money_flow(['300142.XSHE'], start_date='2020-6-16', end_date='2020-9-16', fields=None, count=None)
#获取大单date     sec_code  change_pct  net_amount_main  net_pct_main
df = get_money_flow([code] , start_date = start, end_date = end , fields = ['date','change_pct','net_amount_main','net_pct_main'] , count = None)
df['ma5']=df['net_amount_main'].rolling(5).mean()
df['ma14']=df['net_amount_main'].rolling(14).mean()
df['code'] = code
print(df[['date','code','net_amount_main','ma5','ma14']])




