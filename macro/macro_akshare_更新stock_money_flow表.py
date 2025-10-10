"""
本模块用于批量导入和更新stock_money_flow表
警告：更新前请确保akshare的1分钟数据已更新完毕
"""
from apt.vendor.akshare.money_flow import money_flow as money
from datetime import datetime
import pymysql

# 在开始更新前，先修改MySQL的max_connections参数
def set_max_connections(engine, max_conn=2000):
    """
    设置MySQL的最大连接数
    :param engine: SQLAlchemy引擎对象
    :param max_conn: 最大连接数，默认2000
    """
    connection = None
    try:
        # 获取连接
        connection = engine.raw_connection()
        cursor = connection.cursor()
        
        # 查询当前最大连接数
        cursor.execute("SHOW VARIABLES LIKE 'max_connections'")
        result = cursor.fetchone()
        current_max = int(result[1])
        print(f"当前 max_connections = {current_max}")
        
        # 判断是否需要修改
        if current_max >= max_conn:
            print(f"✓ 当前值({current_max}) >= 目标值({max_conn})，无需修改")
        else:
            print(f"当前值({current_max}) < 目标值({max_conn})，正在修改...")
            # 设置全局最大连接数
            cursor.execute(f"SET GLOBAL max_connections = {max_conn}")
            print(f"✓ 成功设置 max_connections = {max_conn}")
            
            # 再次验证设置
            cursor.execute("SHOW VARIABLES LIKE 'max_connections'")
            result = cursor.fetchone()
            print(f"✓ 验证：新的 max_connections = {result[1]}")
        
        cursor.close()
        
    except Exception as e:
        print(f"⚠ 设置 max_connections 失败: {e}")
        print("提示：可能需要数据库管理员权限(SUPER或SYSTEM_VARIABLES_ADMIN)才能修改此参数")
    finally:
        if connection:
            connection.close()

money = money()

# 设置最大连接数到2000
print("=" * 60)
print("正在设置MySQL最大连接数...")
set_max_connections(money.engine, max_conn=2000)
print("=" * 60)

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