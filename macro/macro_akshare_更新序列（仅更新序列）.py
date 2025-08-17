import numpy as np
import pandas as pd
import tushare as ts
import time
import sys
from datetime import datetime, timedelta
from apt.vendor.tspro.security import security as security
from apt.vendor.akshare.data import data as data
import platform
import os

# 根据操作系统导入不同的音频库
if platform.system() == "Windows":
    import winsound
else:
    # Ubuntu/Linux 使用 os.system 调用 beep 命令
    pass

def run_script():
    # 1. 更新序列
    a = data()
    a.start_date = datetime(2025, 7, 20)
    a.end_date = datetime.now()
    # a.update_etf_day()
    # 优先更新高权限序列 
    a.update_sequence_launch(priority=1, sleep=0.15)
    a.update_sequence_launch(priority=0, sleep=0.15)  # 0.35秒间隔
    #a.fix_1min_error_v3()  # 修复1分钟线数据错误
    #a.update_ak_resample()  # 更新分时线数据（5m和60m重采样）

error_count = 0
max_retries = 20

while error_count < max_retries:
    try:
        run_script()
        break  # 如果脚本成功执行，跳出循环
    except Exception as e:
        error_count += 1
        print(f"Error occurred: {e}. Retrying in 5 seconds. (Attempt {error_count}/{max_retries})")
        time.sleep(1)  # 等待1秒后重试

if error_count >= max_retries:
    print("已达到最大重试次数，程序即将退出。")
    # 发出三声蜂鸣作为语音提醒
    for _ in range(3):
        winsound.Beep(1000, 500)  # 1000Hz, 0.5秒
        time.sleep(0.5)
        break