from jqdatasdk import *
import pandas as pd
import datetime
import sqlalchemy
from apt.vendor.jqdata.jqdata import data as jqdata
from apt.vendor.jqdata.ETF import ETF as ETF

"""
聚宽数据每日更新
日线分时线：
日行情	：盘中实时更新（每3s刷新一次）
分钟行情：盘中实时更新（每3s刷新一次）盘后24:00更新
融资融券	2010至今	下一个交易日10点之前更新
资金流向	2010至今	盘后20:00更新
龙虎榜数据	2005至今	盘后18:00更新
沪深市场每日成交概况	2005年至今	交易日20:30-24:00更新
沪股通，深股通和港股通(市场通数据）	上市至今	交易日20:30-06:30更新
分级基金数据	2005至今	8:00更新
日行情	2005至今	盘中实时更新（每3s刷新一次）
分钟行情	2005至今	盘前9:00更新 盘中实时更新（每3s刷新一次）盘后24:00更新
############场内基金数据	时间范围	更新频率
场内基金列表数据	2005至今	8:00更新
分级基金数据	2005至今	8:00更新
日行情	2005至今	盘中实时更新（每3s刷新一次）
分钟行情	2005至今	盘前9:00更新 盘中实时更新（每3s刷新一次）盘后24:00更新
净值数据	2005至今	下一个交易日10点之前更新
融资融券	2010至今	下一个交易日10点之前更新
场内基金份额数据	2005-02-23至今	下一个交易日10点之前更新
集合竞价数据	2019年至今	交易日最晚9:28分之前更新
"""

start = datetime.datetime(2021,10,15)    #日线 60m 30m 最后更新日10/14含
             #（注意：日线数据不能在过零点及开盘前更新，否则会出现类似于停盘的数据 无VOL MONEY）
                                         #5m 最后更新10/14含
#end = datetime.datetime(2005,12,31,16)
end = datetime.datetime.now()
jq = jqdata(rds_host = jqdata.数据源.localhost , myauth = True )
df_remain = get_query_count()
print(df_remain)
#dd = get_bars('399001.XSHE', end_dt = '2009-11-25',count =24,unit='5m' , fields = ['date', 'open', 'close', 'high', 'low', 'volume', 'money','factor'])
#print(dd)
#更新5分钟线
jq.update_v1(start_date = start , end_date = end , ktype = '5m' )
#更新指数
jq.update_index(start_date = start , end_date = end , ktype = '5m')
jq.update_index(start_date = start , end_date = end , ktype = '30m')
jq.update_index(start_date = start , end_date = end , ktype = '60m')
jq.update_index(start_date = start , end_date = end , ktype = '1d')

#更新日线
jq.update_v2(start_date = start , end_date = end , ktype = '1d' )
#更新60分钟线
jq.update_v2(start_date = start , end_date = end , ktype = '60m' )
#更新30分钟线
jq.update_v2(start_date = start , end_date = end , ktype = '30m' )
