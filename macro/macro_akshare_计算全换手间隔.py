from apt.vendor.tspro.data import data as data
from datetime import datetime
tspro = data()
tspro.start_date= datetime(2023,12,1,8)
tspro.end_date = datetime(2023,12,26,16)
#tspro.update_day()
#tspro.update_day_ETF()
#添加数据
tspro.update_cumulative_turnover()
#更新数据
tspro.analyse_cumulative_turnover()