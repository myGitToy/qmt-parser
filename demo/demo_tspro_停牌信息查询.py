"""
本模块用于演示如何获取tspro中的停牌信息
目前有两种方式可以获取，取到的内容每天数量上保持一致，具体细节略有不同



参考链接：
https://tushare.pro/document/2?doc_id=31
      ts_code suspend_date resume_date             suspend_reason
0   600077.SH     20230614        None                       重要公告
1   000616.SZ     20230614        None                       重大事项
2   002535.SZ     20230614    20230615                   撤销其他风险警示
3   600666.SH     20230614    20230615                       重要公告
4   300526.SZ     20230614    20230619                       重大事项
5   600530.SH     20230614        None                  未如期披露定期报告
6   600393.SH     20230614        None                    重要事项未公告
7   300319.SZ     20230614        None                       重大事项
8   000667.SZ     20230614        None                       重大事项

https://tushare.pro/document/2?doc_id=214
        ts_code suspend_type trade_date suspend_timing
0   000029.SZ            S     20200312           None
1   000502.SZ            S     20200312           None
2   000939.SZ            S     20200312           None
3   000977.SZ            S     20200312           None
4   000995.SZ            S     20200312           None
5   002260.SZ            S     20200312           None
6   002450.SZ            S     20200312           None
7   002604.SZ            S     20200312           None
8   300028.SZ            S     20200312           None
9   300104.SZ            S     20200312           None
10  300216.SZ            S     20200312           None
11  300592.SZ            S     20200312           None
12  300819.SZ            S     20200312    09:30-10:00
13  300821.SZ            S     20200312    09:30-10:00
"""


import numpy as np
import pandas as pd
import tushare as ts
from datetime import datetime,timedelta
from apt.vendor.tspro.security import security  as security
from apt.vendor.tspro.data import data as data
#pd.set_option('display.max_columns', None)
#pd.set_option('display.max_rows', None)
#1. 按日查询停牌信息
pro = ts.pro_api()
#提取2020-03-12的停牌股票
day = datetime(2023,6,16)
df1 = pro.suspend( suspend_date=day.strftime('%Y%m%d'))
print(df1)
df2 = pro.suspend_d(suspend_type='S', trade_date= day.strftime('%Y%m%d'))
print(df2)


#

