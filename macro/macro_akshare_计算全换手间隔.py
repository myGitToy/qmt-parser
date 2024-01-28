from apt.vendor.tspro.data import data as data
from apt.vendor.tspro.cumulative_turnover import cum_turnover as ct
from datetime import datetime
tspro = ct()
#2017-2023数据已导入
tspro.start_date= datetime(2016,1,1,8)
tspro.end_date = datetime(2016,12,31,18)
#tspro.update_day()
#tspro.update_day_ETF()
#添加数据
#tspro.insert_cumulative_turnover()
tspro.update_cumulative_turnover()