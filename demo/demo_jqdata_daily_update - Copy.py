from jqdatasdk import *
import pandas as pd
import datetime
import sqlalchemy
from apt.vendor.jqdata.jqdata import data as jqdata
from apt.vendor.jqdata.ETF import ETF as ETF


start = datetime.datetime(2021,1,6)    #日线 60m 最后更新日12/25 含
                                         #5m 最后更新XX/XX含
                                         #30m 最后更新自2019年起的数据
#end = datetime.datetime(2021,1,18,16)
end = datetime.datetime.now()
code = '515030.XSHG'
jq = jqdata(rds_host = jqdata.数据源.localhost , myauth = True )

df = get_bars(code, end_dt = end , count = 200 ,unit='60m' , fields = ['date', 'open', 'close', 'high', 'low', 'volume', 'money','factor'])
#print(df['close'].rolling(10).quantile(0.75))
df['p75'] = df['close'].rolling(100).quantile(0.75)
df['p85'] = df['close'].rolling(100).quantile(0.85)
df['p90'] = df['close'].rolling(100).quantile(0.90)
df['p95'] = df['close'].rolling(100).quantile(0.95)
df[['date','open','high','low','close','p75','p85','p90','p95']].to_csv('.\\data\\quantile_%s.csv' % code , encoding = 'utf_8_sig')
print(df)
"""
print("中位数：%s" % (format(df['close'].quantile(q=0.5), '.3f')))
print("75%%位置：%s" % (format(df['close'].quantile(q=0.75), '.3f')))
print("85%%位置：%s" % (format(df['close'].quantile(q=0.85), '.3f')))
print("90%%位置：%s" % (format(df['close'].quantile(q=0.90), '.3f')))
print("95%%位置：%s" % (format(df['close'].quantile(q=0.95), '.3f')))
"""