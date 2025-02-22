from jqdatasdk import *
import pandas as pd
import datetime
import sqlalchemy
from apt.vendor.jqdata.jqdata import data as jqdata
#显示所有列
pd.set_option('display.max_columns', None)

#jqdata_60m更新 已完成2018-2020年11月的数据导入
#jqdata_5m更新 已完成2019.7至今的数据
#day = datetime.datetime(2004,1,1)  #2005年之前的数据不存在，聚宽未收录
#end = datetime.datetime(2004,12,31,16)


day = datetime.datetime(2019,11,1)  #未完成
end = datetime.datetime(2019,12,31,16)
#5分钟线更新到12/10日 含
code = '512760.XSHG'

print(datetime.datetime.now())
jq = jqdata()
##########读取更新列表
code_list  = list(get_all_securities(['stock','etf'],date = end).index)
print(len(code_list))
df_remain = get_query_count()
print(df_remain)
#df_TEST = get_bars(security = ['159949.XSHE'] , count = 10 , unit = '5m' , fields = ['date', 'open', 'close', 'high', 'low', 'volume', 'money','factor'] , include_now = False , end_dt = end , df = True)
#print(df_TEST)
#jq.update_byday(start_date = day , code_list = code_list , ktype = '5m' , end_date = end)
jq.update(start_date = day , code_list = code_list , ktype = '5m' , end_date = end)

#动态复权
#df = get_bars(security = code , count = 10, unit = '60m' , fields = ['date', 'open', 'close', 'high', 'low', 'volume', 'money','factor'] , include_now = False , end_dt = day, fq_ref_date = day , df = True)
#不复权
df = get_bars(security = code , count = 60, unit = '60m' , fields = ['date', 'open', 'close', 'high', 'low', 'volume', 'money','factor'] , include_now = False , end_dt = day, df = True)


df['code'] = code
print(df)
engine = sqlalchemy.create_engine('mysql+pymysql://stock_user:a@1#Yy1c@localhost:3306/stock')
#query = "select count(code) as num from ts_tick where code = '%s' and left(time,10)='%s'" % (code,day)
#更新复权数据
#df = pandas.read_sql("select * from your_table;", engine)
df.to_sql('temp_table', engine, if_exists='replace')

sql = "UPDATE jqdata_60m AS f SET factor = t.factor FROM temp_table AS t WHERE f.code = t.code  and t.date = f.date"

with engine.begin() as conn:     # TRANSACTION
        conn.execute(sql)
"""
try:
    df.to_sql(name = 'jqdata_60m',con = engine ,index = False,if_exists = 'append')
except IntegrityError:
    print('已有重复数据')
"""

