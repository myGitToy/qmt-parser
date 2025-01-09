from apt.vendor.akshare.security import security as sec
from datetime import datetime
sec = sec()
sec.code = '600638.sh'
sec.start_date = datetime(2024,1,1)
sec.end_date = datetime(2024,11,1)
df = sec.get_trade_date()
print(df)