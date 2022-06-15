import tushare as ts
import pandas as pd
pro = ts.pro_api('55297f16c0119146589e059db315ba28a9412e89ec9f91e538e655b2')
# 列名与数据对其显示
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
# 显示所有列
pd.set_option('display.max_columns', None)
# 显示所有行
#pd.set_option('display.max_rows', None)

#通用行情接口测试（日线）此接口
print(f'------------日线数据测试-----------')
df_a_day = ts.pro_bar(ts_code = '510300.sh' ,  start_date = '2022-06-01' , end_date = '2022-06-13' , adj = None , adjfactor = True )
print(df_a_day)

#通用行情接口测试（分时线）
#备注 分时线最多返回8000行数据
print(f'------------分时线数据测试-----------')
#df_a_min = ts.pro_bar(ts_code = '159949.sz', start_date = '2021-06-01 09:20:00' , end_date = '2022-06-14 15:10:00' , freq = '1min', adj = None )
#print(df_a_min)

#提取复权因子
df_adj = pro.adj_factor(ts_code='601012.sh', trade_date='')
print(df_adj)

#df_fund = pro.fund_daily(ts_code='510300.SZ', start_date='2022-06-01', end_date='2022-06-13')
#print(df_fund)
