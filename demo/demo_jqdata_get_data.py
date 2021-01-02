from jqdatasdk import *
import pandas as pd
import datetime
import sqlalchemy
from apt.vendor.jqdata.jqdata import data as jqdata
#显示所有列
pd.set_option('display.max_columns', None)  
#测试jqdata获取数据模块
d = jqdata()
auth('13817092632','JQ@tushare123')
day = datetime.datetime(2017,7,10,16)
code = '600519.XSHG'
#动态复权
#df = get_bars(security = code , count = 10, unit = '1d' , fields = ['date', 'open', 'close', 'high', 'low', 'volume', 'money','factor'] , include_now = False , end_dt = day, fq_ref_date = '2020-06-15' , df = True)
df = get_price(security = '600519.XSHG', start_date='2017-07-05', end_date='2017-7-10', frequency='daily',  fq='pre')
print(df)
#不复权
d.get_data(code = '600519.XSHG' , start_date = datetime.datetime(2017,7,5) , end_date = datetime.datetime(2017,7,10) , ktype = '1d' , fq = jqdata.复权.前复权) 