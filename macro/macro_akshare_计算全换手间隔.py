from apt.vendor.tspro.data import data as data
from datetime import datetime
tspro = data()
tspro.start_date= datetime(2020,1,1,8)
tspro.end_date = datetime(2021,12,31,16)
#tspro.update_day()
#tspro.update_day_ETF()
#添加数据
#tspro.update_cumulative_turnover()
#更新数据 2022-2023数据全
#2020-2021正在分析，已导入
tspro.analyse_cumulative_turnover()