"""
本模块用以演示从apt中导入tspro的data模块，并使用gradio进行数据展示
"""
import gradio as gr
import pandas as pd
import numpy as np
from datetime import datetime
from apt.vendor.tspro.data import data as ts_data
# 设置页面标题


# 创建侧边栏菜单

#导入数据
ts = ts_data()
ts.start_date = datetime(2024,7,8,8)
ts.end_date = datetime.now()
ts.code = '600038.sh'
df = ts.get_k_data()

def show_data(code, date_range):
    ts = ts_data()
    ts.start_date = datetime.strptime(date_range[0], "%Y-%m-%d")
    ts.end_date = datetime.strptime(date_range[1], "%Y-%m-%d")
    ts.code = code
    df = ts.get_k_data()
    return df.to_html()  # 使用.to_html()来更好地在网页上展示DataFrame

# 定义代码选择框的选项
codes = ["600038.sh", "000001.sz", "AAPL", "GOOGL"]  # 示例代码列表，根据需要进行修改

# 创建Gradio界面，增加代码选择框和日期选择器
iface = gr.Interface(
    fn=show_data, 
    inputs=[
        gr.Dropdown(choices=codes, label="选择代码"), 
        gr.DatePicker(range=True, label="选择日期范围")
    ], 
    outputs="html", 
    title="日线K线数据展示"
)

# 启动界面
iface.launch()
