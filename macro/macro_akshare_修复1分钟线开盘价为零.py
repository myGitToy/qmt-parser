from apt.vendor.akshare.data import data as data
from datetime import datetime
tspro = data()
tspro.start_date= datetime(2023,12,26,8)
tspro.end_date = datetime.now()
tspro.fix_1min_error_v2()