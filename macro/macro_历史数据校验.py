"""
对数据库的完整性进行校验，目前可以校验的库有：
1. tspro_1d
2. tspro_factor
3. tspro_5m
4. tspro_15m
5. tspro_30m
6. tspro_60m
7. tspro_daily_basic
8. tspro_money_flow
9. tspro_cumulative_turnover
10. tspro_security
11. tspro_security_ETF
12. tspro_calendar
13. 
14. tspro_factor_ETF

备注：
1. 只对大尺度上的数据进行校验，即校验每日的数据量，不对个股是否有数据进行校验
2. 校验的标准为：每日的数据量在X倍标准差范围内(默认为3)
3. 需要实现更新交易日历的功能，否则无法获取最新的交易日历，因此校验可能会出现最新的交易日期无法校验的情况
4. 如果选择的校验日期跨度太大（比如两年），由于标准差可能比较大，因此早年的日期可能无法满足3倍标准差的要求
"""
import pandas as pd
from datetime import datetime
from apt.vendor.tspro.data import data as tsdata
from apt.vendor.tspro.security import security as tssec

def verify_db(verify = tsdata() , sql_string = None , std_dev = 3):
    """
    校验数据完整性
    输入：
        verify 为tsdata()类的实例
        sql_string 为需要校验的sql语句
        std_dev 为标准差倍数，默认为3倍
    """
    #数据校验工作
    #取出日期区间内的交易日
    verify_db = tssec.get_calendar(verify)
    #通过pro_api取得交易日历
    #df_trade_day = verify.pro.trade_cal(exchange = 'SSE', start_date = verify.start_date.strftime('%Y%m%d'), end_date = verify.end_date.strftime('%Y%m%d'))
    #print(verify_db)
    #对数据进行校验，取得每个代码每个日期的数据
    df = pd.read_sql(sql_string,verify.engine)
    #print(df)
    verify_db['num'] = None
    verify_db.update(df)
    #计算num_1d列的标准差
    std= verify_db['num'].std()
    mean = verify_db['num'].mean()
    #如果num_1d列中的数据在3倍标准差范围内，则通过校验，verify_1d置为1
    verify_db['verify'] = None
    verify_db['num'] = verify_db['num'].fillna(0)   #将None替换成0，否则apply将传递None值，这是不允许的
    verify_db['verify'] = verify_db['num'].apply(lambda x: 1 if x > mean - std_dev * std else 0)
    #print(verify_db)
    #检查tspro_1d中校验未通过的数量
    num =verify_db[verify_db['verify'] == 0]
    if num.empty:
        print('校验通过')
    else:
        #输出未通过的列
        print(verify_db[verify_db['verify'] == 0])
    

verify = tsdata()
verify.start_date = datetime(2015,1,1)
verify.end_date = datetime(2015,1,12)

#取出日期区间内的交易日
df_trade_day = tssec.get_calendar(verify)
#

#1. tspro_1d
print("--------开始校验tspro_1d的数据完整性--------")
#对tspor的日线数据进行校验，取得每个代码每个日期的数据
sql = f"select date(date) , count(date) as num from tspro_1d where date >= '{verify.start_date.date()}' and date <= '{verify.end_date.date()}' group by date"
df = verify_db(verify = verify , sql_string = sql , std_dev = 3)

#2. tspro_factor
print("--------开始校验tspro复权因子的数据完整性--------")
#对tspor的日线数据进行校验，取得每个代码每个日期的数据
sql = f"select date(date) , count(date) as num from tspro_factor where date >= '{verify.start_date.date()}' and date <= '{verify.end_date.date()}' group by date"
df = verify_db(verify = verify , sql_string = sql , std_dev = 3)

#3. tspro_basic
print("--------开始校验tspro_basic数据完整性--------")
#对tspor的日线数据进行校验，取得每个代码每个日期的数据
sql = f"select date(date) , count(date) as num from tspro_basic where date >= '{verify.start_date.date()}' and date <= '{verify.end_date.date()}' group by date"
df = verify_db(verify = verify , sql_string = sql , std_dev = 3)

#4. tspro_basic
print("--------开始校验tspro_cumulative_turnover数据完整性--------")
#对tspor的日线数据进行校验，取得每个代码每个日期的数据
sql = f"select date(date) , count(date) as num from tspro_cumulative_turnover where date >= '{verify.start_date.date()}' and date <= '{verify.end_date.date()}' group by date"
df = verify_db(verify = verify , sql_string = sql , std_dev = 3)

#5. tspro_money_flow
print("--------开始校验tspro_money_flow数据完整性--------")
#对tspor的日线数据进行校验，取得每个代码每个日期的数据
sql = f"select date(date) , count(date) as num from tspro_cumulative_turnover where date >= '{verify.start_date.date()}' and date <= '{verify.end_date.date()}' group by date"
df = verify_db(verify = verify , sql_string = sql , std_dev = 3)

#7. tspro_60m
print("--------开始校验akshare_60m的数据完整性--------")
#对tspor的日线数据进行校验，取得每个代码每个日期的数据
sql = f"select date(date) , count(date) as num from akshare_60m where date >= '{verify.start_date.date()}' and date <= '{verify.end_date.date()}' group by date(date)"
df = verify_db(verify = verify , sql_string = sql , std_dev = 3)


