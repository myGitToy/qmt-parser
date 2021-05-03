from jqdatasdk import *
import pandas as pd
import datetime
import sqlalchemy
from apt.vendor.jqdata.jqdata import data as jqdata
from apt.qsp_jqdata.atr import ATR as atr
#显示所有列
pd.set_option('display.max_columns', None)  
#测试jqdata获取数据模块
d = jqdata(myauth = False)
start = datetime.datetime(2020,1,1,8)
end = datetime.datetime(2021,1,4,16)
code = '515030.XSHG'
atr = atr(code = code ,start = start , end = end , ktype = "1d" ,fq = jqdata.复权.动态复权 ,myauth = False)
#dl = atr.get_k_data()
at = atr.get_atr()
at.to_csv('.\\data\\%s_20210104_%s.csv' % (code,'1d'), encoding = 'utf_8_sig')
print(at)

df = d.get_k_data(code = code ,start_date = start , end_date = end, ktype = '60m' , fq = d.复权.动态复权)
print(df)
#动态复权
#df = get_bars(security = code , count = 10, unit = '1d' , fields = ['date', 'open', 'close', 'high', 'low', 'volume', 'money','factor'] , include_now = False , end_dt = day, fq_ref_date = '2020-06-15' , df = True)
df = get_price(security = '600519.XSHG', start_date='2017-07-05', end_date='2017-7-10', frequency='daily',  fq='pre')

#不复权
d.get_data(code = '600519.XSHG' , start_date = datetime.datetime(2017,7,5) , end_date = datetime.datetime(2017,7,10) , ktype = '1d' , fq = jqdata.复权.前复权) 