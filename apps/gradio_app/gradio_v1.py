import gradio as gr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from apt.vendor.tspro.data import data as data
from datetime import datetime

"""
测试 gradio 框架
页面有以下几个交互界面：
1. 一个文本框，用于输入证券代码 code
2. 两个日期选择框，用于输入开始日期start_date和结束日期end_date
3. 一个下拉框，用于选择K线类型 ktype
4. 一个下拉框，用于选择复权类型 fqtype
5. 一个按钮，用于提交表单
"""
def submit_form(code, start_date, end_date, ktype, fqtype):
    """
    获取用户输入的表单，返回证券OHLC数据
    """
    ts = data()
    ts.code = code
    # 将时间戳转换为日期字符串
    start_date = datetime.fromtimestamp(float(start_date)).strftime('%Y-%m-%d')
    end_date = datetime.fromtimestamp(float(end_date)).strftime('%Y-%m-%d')   
    # 将字符串转换为日期对象
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")    
    ts.start_date = start_date
    ts.end_date = end_date
    df = ts.get_k_data()
    #ts.ktype = ktype

    # 调用 plot_k_line 函数
    k_line_image = plot_k_line(df)
    return df ,k_line_image

def plot_k_line(df):
    """
    根据输入的OHLC数据绘制K线图
    """    
    fig, ax = plt.subplots()
    print(df)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    df['color'] = np.where(df['close'] >= df['open'], 'g', 'r')
    
    for idx, row in df.iterrows():
        color = row['color']
        ax.plot([idx, idx], [row['low'], row['high']], color=color)
        ax.plot([idx, idx], [row['open'], row['close']], color=color, linewidth=6)
    
    plt.xticks(rotation=45)
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.title('K Line Chart')
    plt.grid(True)
    
    # 保存图像到文件
    plt.savefig('k_line_chart.png')
    plt.close(fig)
    return 'k_line_chart.png'

# 使用 gradio 的新 API
with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column(scale=1):
            #左侧1/3
            code_input = gr.Textbox(label="证券代码", value="600638.SH")
            start_date_input = gr.components.DateTime(label="开始日期", value="2024-07-01 00:00:00")
            end_date_input = gr.components.DateTime(label="结束日期", value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            ktype_dropdown = gr.Dropdown(choices=["1d", "1w", "1m"], label="K线类型", value="1d")
            fqtype_dropdown = gr.Dropdown(choices=["qfq", "hfq"], label="复权类型", value="qfq")
            submit_button = gr.Button("提交", size="small")
        with gr.Column(scale=2):
            #输出的数据框 右侧2/3
            k_data_output = gr.Dataframe(visible=True)
            #输出的K线图
            k_line_image = gr.Image(label="K线图")
    #提交按钮并绘制K线
    submit_button.click(fn=submit_form, inputs=[code_input, start_date_input, end_date_input, ktype_dropdown, fqtype_dropdown], outputs=[k_data_output ,k_line_image])
    #绘制K线（这里拆开来绘制会有问题，由于是异步的方式，这里的dataframe初始是空值，因此OHLC数据处理会报错）
    #解决方案，将两个函数合并到一个函数中，submit_button.click一次调用两个函数并返回两个控件的值
    #submit_button.click(fn=plot_k_line, inputs=k_data_output, outputs=k_line_image)
"""
老的界面代码
demo = gr.Interface(
    fn=submit_form,
    inputs=[code_input, start_date_input, end_date_input, ktype_dropdown, fqtype_dropdown],
    outputs=gr.DataFrame()
    )
"""
if __name__ == "__main__":
    demo.launch()