#tushare的增减持
import pandas as pd
import calendar
import tushare as ts
from datetime import datetime,timedelta
from apt.vendor.tspro.pro_api import pro_api
from apt.vendor.tspro.pro_api import pro_api
from dateutil.relativedelta import relativedelta

def get_change(row, extra_arg):
    """
    【输入】：
        row: 一行数据，DataFrame 类型 必须包含code，base_start_date，base_end_date三列
        extra_arg: 额外参数，可以是任意类型，由用户传入
            默认的参数有：用于比较的基准代码 base_code；month_name：第x月，一般是数字1,3,6,12
            
    【输出】：
        一行数据，DataFrame 类型，包含返回的列名，一般有两个，M(x)_change_pct, M(x)_change_pct(base_code)
    """
    # 假设 a.get_k_data() 返回一个包含 'change' 列的 DataFrame
    a = pro_api()
    a.code = row['code']
    a.start_date = row['base_start_date']
    a.end_date = row['base_end_date']
    a.ktype = '1d'
    df = a.get_k_data()
    #构造返回值
    #涨跌幅等于dataframe中第一个行和最后一行收盘价的差值百分比
    df['change'] = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]
    change = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]
    rst = pd.DataFrame()
    #将change的值赋值给rst
    rst['change'] = change
    #rst['change'] =  (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]
    #print(rst['change'])
    #df['M' + str(extra_arg) + '_change_pct'] = df['change'].sum()
    #return df['change'].sum()
    return change

a = pro_api()
a.start_date = datetime(2021,3,1,8)
a.end_date = datetime(2024,3,20,16)
a.code = '600519.SH'
a.ktype = '1d'
df = a.stk_holdertrade()
#数据汇总，按照date,in_de,holder_type进行汇总，date按月汇总
df['date'] = df['date'].apply(lambda x: x.strftime('%Y-%m'))
df_tspro_group = df.groupby(['code','date','in_de','holder_type'])[['change_vol','money','change_ratio']].sum().reset_index()
#change_vol转换成手
df_tspro_group['change_vol'] = df_tspro_group['change_vol'] / 100
#money转换成万元
df_tspro_group['money'] = df_tspro_group['money'] / 10000
#change_vol取整
df_tspro_group['change_vol'] = df_tspro_group['change_vol'].round(0)
#其他输出的结果保留小数点后两位
df_tspro_group['money'] = df_tspro_group['money'].round
#df_tspro_group['money'] = pd.to_numeric(df_tspro_group['money'], errors='coerce').round(2)
df_tspro_group['change_ratio'] = df_tspro_group['change_ratio'].round(2)
#输出结果
#print(df_tspro_group[['code','date','holder_type','in_de','change_vol','money','change_ratio']])
#计算当月的涨跌幅
#获取当月第一天的数据
df_tspro_group['date'] = pd.to_datetime(df_tspro_group['date'])
#df_tspro_group['year'] = df_tspro_group['date'].dt.year
#df_tspro_group['month'] = df_tspro_group['date'].dt.month
#df_tspro_group['day'] = df_tspro_group['date'].dt.day
df_tspro_group['first_day'] = df_tspro_group['date'].apply(lambda x: datetime(x.year,x.month,1))
df_tspro_group['first_day'] = pd.to_datetime(df_tspro_group['first_day'])
#获取当月最后一天的数据
df_tspro_group['last_day'] = df_tspro_group['date'].apply(lambda x: datetime(x.year, x.month, calendar.monthrange(x.year, x.month)[1]) - timedelta(days=1))
df_tspro_group['last_day'] = pd.to_datetime(df_tspro_group['last_day'])
#print(df_tspro_group)
#获取当月的收盘价
month_list = [1,3,6,12]

for month in month_list:
    #获取基准日的日期（当月的第一天为基准日）【另一种算法为当月最后一天为基准月】
    df_tspro_group['base_start_date'] = df_tspro_group['first_day']
    df_tspro_group['base_end_date'] = df_tspro_group['base_start_date'].apply(lambda x: x + relativedelta(months=month))
    #print(df_tspro_group)
    extra_arg = month
    df_tspro_group[f'M{month}_ROC'] = df_tspro_group.apply(get_change, args=(extra_arg,), axis=1)
    
    #收盘价的涨跌幅等于两个日期间的收盘价的差值
#输出结果 包含所有的ROC列
#显示所有的列
pd.set_option('display.max_columns', None)
print(df_tspro_group[['code','date','money','M1_ROC','M3_ROC','M6_ROC','M12_ROC']])
"""
base = pro_api()
base.code = a.code
base.start_date = df_tspro_group['base_start_date']
base.end_date  =  df_tspro_group['base_end_date']
base_close_diff = a.get_k_data()
df_tspro_group['code_close_pct'] = 1
#print(df_tspro_group['code_close_pct'] )

df_tspro_group['change'] =  df_tspro_group.apply(get_change, args=(extra_arg,), axis=1)

"""