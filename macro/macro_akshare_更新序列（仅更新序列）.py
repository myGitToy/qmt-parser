import numpy as np
import pandas as pd
import tushare as ts
import time
import sys                                                                    
from datetime import datetime,timedelta
from apt.vendor.tspro.security import security  as security
from apt.vendor.akshare.data import data as data
def run_script():
    #1. 更新序列
    a = data()
    a.start_date= datetime(2021,6,1)
    a.end_date = datetime.now()
    #a.update_etf_day()
    #优先更新高权限序列 
    a.update_sequence_launch(priority = 1 , sleep = 0.00)
    a.update_sequence_launch(priority = 0 , sleep = 0.01) 

while True:
    try:
        run_script()
        break  # 如果脚本成功执行，跳出循环
    except Exception as e:
        print(f"Error occurred: {e}. Retrying in 5 seconds.")
        time.sleep(5)  # 等待5秒后重试

