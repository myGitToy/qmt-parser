from apt.vendor.tspro.data import data as data
from datetime import datetime
tspro = data()
#2019-2023数据已导入
tspro.start_date= datetime(2018,1,1,8)
tspro.end_date = datetime(2018,12,31,18)
#tspro.update_day()
#tspro.update_day_ETF()
#添加数据
#tspro.update_cumulative_turnover()
tspro.analyse_cumulative_turnover()