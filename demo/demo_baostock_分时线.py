"""
证券宝 baostock
http://baostock.com/baostock/index.php/A%E8%82%A1K%E7%BA%BF%E6%95%B0%E6%8D%AE
目前无法获取1分钟线，5分钟起步，数据自1990年起
"""

import baostock as bs
import pandas as pd
#### 登陆系统 ####
lg = bs.login()
# 显示登陆返回信息
print('login respond error_code:'+lg.error_code)
print('login respond  error_msg:'+lg.error_msg)

#### 获取沪深A股历史K线数据 ####
# 详细指标参数，参见“历史行情指标参数”章节；“分钟线”参数与“日线”参数不同。“分钟线”不包含指数。
# 分钟线指标：date,time,code,open,high,low,close,volume,amount,adjustflag
# 周月线指标：date,code,open,high,low,close,volume,amount,adjustflag,turn,pctChg
rs = bs.query_history_k_data_plus("sh.601318",
    "date,time,code,open,high,low,close,volume,amount,adjustflag",
    start_date='2020-01-01', end_date='2025-12-31',
    frequency="1", adjustflag="3")
print('query_history_k_data_plus respond error_code:'+rs.error_code)
print('query_history_k_data_plus respond  error_msg:'+rs.error_msg)
print(rs)
#### 打印结果集 ####
data_list = []
while (rs.error_code == '0') & rs.next():
    # 获取一条记录，将记录合并在一起
    data_list.append(rs.get_row_data())
result = pd.DataFrame(data_list, columns=rs.fields)

# 删除date列
if 'date' in result.columns:
    result = result.drop('date', axis=1)

# 将time列格式从20250710093500000转换为2025-07-11 13:30:00
if 'time' in result.columns:
    result['time'] = pd.to_datetime(result['time'], format='%Y%m%d%H%M%S%f').dt.strftime('%Y-%m-%d %H:%M:%S')
    result = result.rename(columns={'time': 'date'})
    #result['date'] = pd.to_datetime(result['date'])

#### 结果集输出到csv文件 ####   
result.to_csv("D:\\history_A_stock_k_data.csv", index=False)
print(result)

#### 登出系统 ####
bs.logout()