from apt.vendor.akshare.data import data as data
from datetime import datetime
akdata = data()
akdata.start_date= datetime(2025,7,21,8)
akdata.end_date = datetime.now()
#akdata.fix_1min_error_v2() #第二版采用1m和5m的数据做对比，自2025/4起东财做了更新限制，目前比较难获取5m数据，因此后续将会修改
akdata.fix_1min_error_v3()
akdata.update_ak_resample()