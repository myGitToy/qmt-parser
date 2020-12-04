from jqdatasdk import *
import pandas as pd
import datetime
import sqlalchemy
from apt.vendor.jqdata.jqdata import jqdata as jqdata
#显示所有列
pd.set_option('display.max_columns', None)
#auth('13817092632','JQ@tushare123')
#jqdata_60m更新 已完成2018-2020年11月的数据导入
day = datetime.datetime(2004,1,1) 
end = datetime.datetime(2004,12,31,16)
code = '512760.XSHG'

print(datetime.datetime.now())
jq = jqdata()
##########读取更新列表
code_list  = list(get_all_securities(['stock','etf'],date = end).index)
print(len(code_list))
jq.jqdata_update_v2(start_date = day , code_list = code_list , ktype = '60m' , end_date = end)

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

