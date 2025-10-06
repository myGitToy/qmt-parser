from apt.vendor.akshare.money_flow import money_flow as money
from datetime import datetime
money = money()
money.start_date = datetime(2023,12,4)
money.end_date = datetime.now()
money.ktype = '1m'
# 更新基于1分钟数据的资金流向表
# 备注：更新前请确保akshare的1分钟数据已更新完毕
# 弹出对话框确认
import tkinter as tk
from tkinter import messagebox
root = tk.Tk()
root.withdraw()  # 隐藏主窗口
if messagebox.askyesno("确认", "请确保akshare的1分钟数据已更新完毕，是否继续更新stock_money_flow表？"):
    money.update_money_flow_min()
else:
    print("操作已取消，未更新stock_money_flow表。")