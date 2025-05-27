from apt.vendor.akshare.data import data as data
from datetime import datetime
akdata = data()
akdata.start_date= datetime(2025,5,10,8)
akdata.end_date = datetime.now()
akdata.fix_1min_error_v2()
