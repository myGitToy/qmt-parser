from apt.vendor.akshare.data import data as data
from datetime import datetime
akdata = data()
akdata.start_date= datetime(2024,6,20,8)
akdata.end_date = datetime(2024,6,20,18)
akdata.fix_1min_error_v2()