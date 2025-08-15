import streamlit as st
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import datetime


# 将工作区根目录添加到sys.path中
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))
from apt.vendor.tspro.data import data as ts_data

# 设置页面标题
st.title('我的Streamlit应用')

# 创建侧边栏菜单
menu = st.sidebar.selectbox('菜单', ['首页', '数据分析', '关于'])
# 生成随机数据
ts = ts_data()
ts.start_date = datetime(2024,7,8,8)
ts.end_date = datetime.now()
ts.code = '600038.sh'
data = ts.get_k_data()
"""

pd.DataFrame({
  '日期': pd.date_range(start='1/1/2022', periods=100),
  '销售额': np.random.randn(100).cumsum()
})
"""
# 二级菜单的逻辑
if menu == '数据分析':
    submenu = st.sidebar.radio('数据分析选项', ['销售数据', '客户数据'])
    # 显示一个按钮
    if st.button('点击我'):
        st.write('按钮被点击了！')
        
    if submenu == '销售数据':
        # 显示数据表
        st.write("## 销售数据", data)

        # 创建一个图表
        st.line_chart(data.set_index('date'))

        # 添加一个滑块
        days = st.slider('选择日期范围', 1, 100, 30)

        # 根据滑块的值筛选数据
        filtered_data = data.head(days)

        # 显示筛选后的数据
        st.write(f"## 最近 {days} 天的销售数据", filtered_data)

        # 显示筛选后的数据的图表
        st.line_chart(filtered_data.set_index('date'))
    elif submenu == '客户数据':
        # 这里添加处理客户数据的代码
        st.write("## 客户数据", "这里显示客户数据...")
elif menu == '关于':
    st.write("## 关于", "这是一个示例Streamlit应用。")
    token = st.text_input("请输入token", value="XXXX")
# 如果选择的是首页，可以在这里添加首页内容
elif menu == '首页':
    st.write("## 欢迎", "欢迎来到我的Streamlit应用！")

