"""
需求：用1m线来拟合60m线，每天60m有四个时间段的数据，date分别是10:30:00 11:30:00 14:00:00 15:00:00
"""

import pandas as pd
from apt.vendor.akshare.data import data as ak_data
from datetime import datetime
ak_data = ak_data()
ak_data.start_date = datetime(2025, 1, 1)
ak_data.end_date = datetime(2025, 4, 19)
ak_data.code = '159949.SZ'  # 示例股票代码
ak_data.ktype = '1m'  # 获取1分钟K线数据
ak_data.fq = ak_data.复权.不复权
df_1m = ak_data.get_k_data()
print(df_1m)
# 假设df_1m是你的1分钟K线数据，包含['date', 'open', 'high', 'low', 'close', 'volume','money']等列
# 'date'列为datetime类型

# 1. 设定目标时间点
target_times = ['10:30:00', '11:30:00', '14:00:00', '15:00:00']

# 2. 提取日期和时间
df_1m['date_only'] = df_1m['date'].dt.date
df_1m['time_only'] = df_1m['date'].dt.strftime('%H:%M:%S')

# 3. 聚合出每个交易日的目标时间段
result = []
for day, group in df_1m.groupby('date_only'):
    for t in target_times:
        # 取当天从09:30到当前目标时间t之间的所有1m数据
        end_time = pd.to_datetime(f"{day} {t}")
        start_time = group['date'].min()
        mask = (group['date'] > start_time) & (group['date'] <= end_time)
        sub = group[mask]
        if not sub.empty:
            row = {
                'date': end_time,
                'open': sub.iloc[0]['open'],
                'high': sub['high'].max(),
                'low': sub['low'].min(),
                'close': sub.iloc[-1]['close'],
                'volume': sub['volume'].sum(),
                'money': sub['money'].sum()
            }
            result.append(row)

df_60m = pd.DataFrame(result)
print(df_60m)