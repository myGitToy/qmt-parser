from jqdatasdk import *
import pandas as pd
import datetime
import sqlalchemy
"""
演示通过日线数据获取复权因子，并将其更新至日线和分时线数据库中
注意：
1. 日线分时线储存的是未复权的原始数据
2. 历史复权因子随着每次复权都会变动，因此需要实时进行更新
3. 本函数可以一次性更新，使用的是inner join的方法
"""
#显示所有列
pd.set_option('display.max_columns', None)
auth('13817092632','JQ@tushare123')
day = datetime.datetime(2020,9,8,16)
code = '159949.XSHE'
df_remain = get_query_count()
print(df_remain)
#动态复权
#df = get_bars(security = code , count = 10, unit = '60m' , fields = ['date', 'open', 'close', 'high', 'low', 'volume', 'money','factor'] , include_now = False , end_dt = day, fq_ref_date = day , df = True)
#不复权
df_jqdata = get_bars(security = '159949.XSHE' , count = 20 , unit = '1d' , fields = ['date', 'open', 'close', 'high', 'low', 'volume', 'money','factor'] , include_now = False , end_dt = day , df = True)
print(df_jqdata)
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

