from jqdatasdk import *
import pandas as pd
import datetime
import sqlalchemy
from apt.vendor.jqdata.jqdata import data as jqdata
from apt.qsp_jqdata.atr import ATR as atr
#显示所有列
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)  
#测试jqdata获取数据模块
d = jqdata(myauth =True)
start = datetime.datetime(2021,2,23,8)
end = datetime.datetime(2021,3,11,16)
code = '512170.XSHG'

#动态复权
df = get_bars(security = code , count = 20, unit = '1d' , fields = ['date', 'open', 'close', 'high', 'low', 'volume', 'money','factor'] , include_now = False , end_dt = end, fq_ref_date = end , df = True)
#df = get_price(security = '600519.XSHG', start_date='2017-07-05', end_date='2017-7-10', frequency='daily',  fq='pre')

#不复权
#d.get_data(code = '600519.XSHG' , start_date = datetime.datetime(2017,7,5) , end_date = datetime.datetime(2017,7,10) , ktype = '1d' , fq = jqdata.复权.前复权) 

print(df[['date','close','factor']])
