from apt.vendor.tspro.data import data as data
from apt.vendor.tspro.cumulative_turnover import cum_turnover as ct
from datetime import datetime
import time
def run_script():
    tspro = ct()
    #全换手区间数据导入：2005-2023
    #全换手区间数据计算：2005-2023，目前正在计算
    #价格区间数据计算：2008-2024.3.1含，目前正在计算
    tspro.start_date= datetime(2025,7,21,8)
    tspro.end_date = datetime.now()
    #tspro.update_day()
    #tspro.update_day_ETF()

    
    #添加数据
    #插入数据
    tspro.insert_cumulative_turnover()
    #更新数据
    tspro.update_cumulative_turnover()    
    #更新日线全换手区间
    tspro.update_price_range_1d()
    #更新1分钟线全换手区间


#测试模式
#run_script()

#正式模式
while True:
    try: 
        
        run_script()
        break  # 如果脚本成功执行，跳出循环
    except Exception as e:
        print(f"Error occurred: {e}. Retrying in 5 seconds.")
        time.sleep(5)  # 等待5秒后重试