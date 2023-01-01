import numpy as np
import pandas as pd
import tushare as ts
from datetime import datetime,timedelta
from apt.vendor.tspro.security import security  as security
from apt.vendor.tspro.data import data as data

#1. 初始化
a = data(myauth = True)
a.code ='600038.sh'
a.start_date= datetime(2021,12,1,1) #1998/10/20日开始有ETF数据    ETF日线数据2000/13/30 ETF复权因子2000/13/32
a.end_date = datetime(2022,1,1,1)
#现在更新2021年的1分钟线数据
#备注 2020年数据centos9数据库是没有的
"""
date	num
2021-01-04	1092212
2021-01-05	1092212
2021-01-06	1092935
2021-01-07	1093658
2021-01-08	1093658
2021-01-11	1094140
2021-01-12	1094863
2021-01-13	1095104
2021-01-14	1095104
2021-01-15	1095345
2021-01-18	1100165
2021-01-19	1101611
2021-01-20	1103780
2021-01-21	1104503
2021-01-22	1105949
2021-01-25	1107154
2021-01-26	1107395
2021-01-27	1108359
2021-01-28	1109805
2021-01-29	1110528
2021-02-01	1111251
"""

#4. 更新股票小时线数据   60分钟线最后更新日期2022/7/6含；1分钟线2020全年写入更新序列
#目前更新序列剩余18700，预计耗时13小时（每分钟预计可更新24-27组，每组约5800条左右）
#每个月数据量约1.5GB（纯数据库 不含索引） 含索引约2.2GB/月

#centos1分钟线数据更新，约每分钟19组 每组5000条左右（1个月的数据量）
#2023/1/1 目前本地局域网更新速度为16.6条/分钟
a.ktype = '1m'
a.update_sequence_add(myclass = 'stock' , type = '1m' , priority = 0)

#6. 更新ETF小时线数据
a.update_sequence_add(myclass = 'etf' , type = '1m' , priority = 0) 