"""
本模块用于分析整体市场资金流向:
1. 基于每只股票的OHLC和成交金额计算资金流入/流出
2. 聚合计算整体市场资金流向
3. 分析大盘资金流向与指数涨跌的关系
4. 可视化展示资金流向与指数变化
我设计了一个公式，每天最高价-最低价作为100%，作为分母，收盘价-开盘价为分子，计算比率，
用这个比率乘以成交金额作为资金流入流出的数据，你觉得合理吗？背后的数学逻辑是什么

波动比率 = (收盘价 - 前收盘价) / (最高价 - 最低价)

这个比率反映了当天价格变动的方向和强度。收盘价高于前收盘价，说明资金偏流入，反之则偏流出。
分母用当天的最高-最低价，代表当天的价格波动区间，归一化处理，避免不同股票或不同天的绝对价格影响。
成交金额

代表当天市场实际交易的资金总量，是资金流动的“体积”。
两者相乘

波动比率体现了资金流向的“方向和强度”，成交金额体现了“规模”。
相乘后，得到的“净资金流向”就是当天资金流入或流出的估算值，单位为资金（如万元、百万元等）。
数学逻辑：

如果当天收盘价大幅高于前收盘价，且成交金额大，说明有大量资金流入；
如果收盘价低于前收盘价，且成交金额大，说明有大量资金流出；
用波动比率归一化后，可以比较不同股票或不同时间的资金流向强度。
本质上，这是一种用价格变动方向和成交金额结合，估算市场资金流入/流出的简化模型。它不能完全反映真实资金流动，但能反映市场情绪和资金活跃度的变化趋势。

V2版本 本演示基于akshare 1m数据计算资金流向，再聚合到日线进行输出，因此资金数据会更加准确
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
from apt.vendor.tspro.data import data as tspro_data
from apt.vendor.akshare.data import data as ak_data
from apt.vendor.akshare.money_flow import money_flow as ak_money
import akshare as ak
from datetime import datetime, timedelta
from tqdm import tqdm
import os
import gradio as gr
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
# dataframe显示设置，显示在一行
pd.set_option('display.max_columns', None)  # 显示所有列
pd.set_option('display.max_rows', None)  # 显示所有行
pd.set_option('display.width', 1000)  # 设置显示宽度
pd.set_option('display.float_format', lambda x: '%.2f' % x)  # 设置浮点数格式


class CapitalFlowAnalyzer(ak_money):
    def __init__(self):
        """初始化个股资金流向分析器"""
        self.stock_data = {}  # 存储各股票数据
        self.daily_capital_flow = {}  # 每日资金流向
        self.daily_sector_flow = {}  # 每日行业板块资金流向
        super().__init__()
        
    def calculate_single_stock_flow(self):
        """计算单只股票的资金流向"""
        # 复制数据以避免修改原始数据
        df = self.stock_data.copy()
        
        # 计算波动比率：(收盘价-开盘价)/(最高价-最低价)
        df['prev_close'] = df['close'].shift(1)
        df['波动比率'] = df.apply(
            lambda row: (row['close'] - row['prev_close']) / (row['high'] - row['low'])
            if (row['high'] != row['low'] and pd.notnull(row['prev_close'])) else 0, axis=1
        )
        
        # 计算资金流向：波动比率 * 成交金额
        df['净资金流向'] = df['波动比率'] * df['money']
        
        # 转换单位和保留小数点位数
        df['净资金流向'] = (df['净资金流向'] / 1000000).round(1)  # 转换为百万并保留1位小数
        df['波动比率'] = df['波动比率'].round(2)  # 波动比率保留2位小数
        
        # 为了保持与之前代码的一致性，还可以计算积极流入和消极流出
        df['积极流入'] = df['净资金流向'].apply(lambda x: x if x > 0 else 0)
        df['消极流出'] = df['净资金流向'].apply(lambda x: -x if x < 0 else 0)
        
        return df

def analyze_stock_capital_flow(stock_code, ktype):
    """分析单只股票的资金流向并返回结果用于Gradio界面"""
    try:
        # 创建分析器实例
        analyzer = CapitalFlowAnalyzer()
        analyzer.code = stock_code.strip()  # 去除可能的空格
        analyzer.start_date = datetime(2025, 1, 1)  # 起始日期，可调整
        analyzer.end_date = datetime.now()  # 结束日期
        analyzer.ktype = ktype.strip().lower() if isinstance(ktype, str) else '1m'
        if analyzer.ktype not in {'1m', '5m', '60m', '1d'}:
            analyzer.ktype = '1m'
        
        # 获取股票数据
        analyzer.stock_data = analyzer.calculate_money_flow_min()
        
        # 调试信息，检查数据是否正确获取
        print(f"获取到的数据行数: {len(analyzer.stock_data)}")
        if len(analyzer.stock_data) > 0:
            print(f"日期范围: {analyzer.stock_data['date'].min()} - {analyzer.stock_data['date'].max()}")
        else:
            print("警告：未获取到任何数据")
            return pd.DataFrame({'错误': ['未获取到任何交易数据']}), go.Figure()
        
        # 根据数据源类型决定聚合方式
        stock_df = analyzer.stock_data.copy()
        if analyzer.ktype in {'1m', '5m', '60m'}:
            flow_data = stock_df.resample('1D', on='date').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'money': 'sum',
                '净资金流向': 'sum'
            }).dropna().reset_index()
        else:
            # 1d 数据无需再聚合，确保字段齐全并排序
            flow_data = stock_df.sort_values('date').reset_index(drop=True)
            # 对于日线数据，若缺少净资金流向字段，则计算一次
            if '净资金流向' not in flow_data.columns:
                flow_data['净资金流向'] = (flow_data['close'] - flow_data['open']) / (
                    flow_data['high'] - flow_data['low']
                ).replace([np.inf, -np.inf], 0).fillna(0) * flow_data['money']

        # 按要求：聚合后重新计算波动比率 = 聚合后的净资金流向 / money
        # 避免除以0并处理无穷大/空值，最终保留两位小数
        flow_data['波动比率'] = np.where(
            flow_data['money'] != 0,
            flow_data['净资金流向'] / flow_data['money'],
            0
        )
        flow_data['波动比率'] = flow_data['波动比率'].replace([np.inf, -np.inf], 0).fillna(0).round(2)

        # 调试信息，检查聚合后的数据
        print(f"聚合后的数据行数: {len(flow_data)}")
        print(flow_data)
        
        # 获取可视化所需数据
        result_df = flow_data[['date', 'open', 'close', 'high', 'low', 'money', '净资金流向', '波动比率']]
        result_df = result_df.tail(120)  # 最近60个交易日，可调整

        # 确保列名和数据格式正确
        print(f"处理后数据行数: {len(result_df)}")

        # 创建图表 - 只针对单一股票，不需要基准指数比较
        fig = create_single_stock_figure(result_df, stock_code)

        # 返回数据表格和图表
        return result_df, fig
        
    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        traceback.print_exc()  # 打印详细错误堆栈
        return pd.DataFrame({'错误': [str(e)]}), go.Figure()

def create_single_stock_figure(data, stock_code):
    """创建单一股票的K线图和资金流向图"""
    # 检查数据是否有效
    if len(data) == 0:
        print("警告：没有数据可供绘图")
        fig = go.Figure()
        fig.update_layout(title="没有数据可供显示")
        return fig
    
    # 确保日期格式正确
    if not pd.api.types.is_datetime64_any_dtype(data['date']):
        data['date'] = pd.to_datetime(data['date'])
        print("已将日期转换为datetime格式")
    
    print(f"绘图数据样本:\n{data[['date', 'open', 'close', 'high', 'low']].head()}")
    
    # 创建包含四个子图的图表，将成交额单独拆分为子图
    try:
        fig = make_subplots(
            rows=4,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.04,
            row_heights=[0.45, 0.2, 0.15, 0.2],
            specs=[[{}], [{}], [{}], [{}]]
        )
        
        # 添加K线图
        fig.add_trace(
            go.Candlestick(
                x=data['date'],
                open=data['open'], 
                high=data['high'],
                low=data['low'], 
                close=data['close'],
                name='K线',
                increasing_line_color='red',  # 上涨K线颜色
                decreasing_line_color='green',  # 下跌K线颜色
                increasing_fillcolor='red',  # 上涨K线填充色
                decreasing_fillcolor='green'  # 下跌K线填充色
            ),
            row=1, col=1
        )
        
        # 计算EMA均线
        ema_periods = [5, 10, 20, 60]
        ema_colors = ['purple', 'orange', 'blue', 'cyan']
        
        for period, color in zip(ema_periods, ema_colors):
            if len(data) >= period:  # 确保数据足够计算均线
                ema = data['close'].ewm(span=period, adjust=False).mean()
                fig.add_trace(
                    go.Scatter(
                        x=data['date'],
                        y=ema,
                        name=f'EMA{period}',
                        line=dict(color=color, width=1)
                    ),
                    row=1, col=1
                )
        
        # 添加成交额柱状图（以亿元为单位）
        volume_colors = ['red' if close >= open else 'green'
                         for close, open in zip(data['close'], data['open'])]

        fig.add_trace(
            go.Bar(
                x=data['date'],
                y=(data['money'] / 100000000),  # 转换为亿元
                name='成交额(亿元)',
                marker_color=volume_colors,
                opacity=0.4,
                marker_line_width=0
            ),
            row=2, col=1
        )

        # 添加波动比率柱状图
        colors_ratio = ['red' if x > 0 else 'green' for x in data['波动比率']]
        fig.add_trace(
            go.Bar(
                x=data['date'],
                y=data['波动比率'],
                name='波动比率',
                marker_color=colors_ratio
            ),
            row=3, col=1
        )

        # 添加参考线表示±0.25和0
        fig.add_shape(
            type="line", line=dict(dash="dash", color="gray"),
            x0=data['date'].iloc[0], y0=0,
            x1=data['date'].iloc[-1], y1=0,
            row=3, col=1
        )
        fig.add_shape(
            type="line", line=dict(dash="dot", color="red", width=1),
            x0=data['date'].iloc[0], y0=0.25,
            x1=data['date'].iloc[-1], y1=0.25,
            row=3, col=1
        )
        fig.add_shape(
            type="line", line=dict(dash="dot", color="green", width=1),
            x0=data['date'].iloc[0], y0=-0.25,
            x1=data['date'].iloc[-1], y1=-0.25,
            row=3, col=1
        )
        
        # 添加日资金流向柱状图
        colors_flow = ['red' if x > 0 else 'green' for x in data['净资金流向']]
        fig.add_trace(
            go.Bar(
                x=data['date'], 
                y=data['净资金流向'] / 100000000,  # 转换为亿元
                name='日资金流向(亿元)', 
                marker_color=colors_flow
            ),
            row=4, col=1
        )
        
        # 累计资金流向
        cumulative_flow = (data['净资金流向'] / 100000000).cumsum()
        fig.add_trace(
            go.Scatter(
                x=data['date'], 
                y=cumulative_flow,
                name='累计资金流向(亿元)', 
                line=dict(color='black')
            ),
            row=4, col=1
        )
        
        # 更新布局
        fig.update_layout(
            title=f'{stock_code} 股票资金流向与波动比率分析',
            height=1000,  # 增加高度以适应四个子图
            template="plotly_white",
            xaxis_rangeslider_visible=False
        )
        
        # 处理交易日期，使K线连续
        if len(data) > 1:
            # 方法1：识别所有非交易日
            data_dates = set(data['date'].dt.date)  # 转换为日期对象而非datetime
            
            # 获取整个日期范围
            min_date = data['date'].min().date()
            max_date = data['date'].max().date()
            
            # 生成期间所有的日期
            all_dates = set()
            curr_date = min_date
            while curr_date <= max_date:
                all_dates.add(curr_date)
                curr_date += timedelta(days=1)
            
            # 找出所有非交易日
            non_trading_days = all_dates - data_dates
            
            # 构建rangebreaks
            breaks = []
            
            # 跳过周末
            breaks.append(dict(bounds=["sat", "mon"]))
            
            # 将非交易日日期按连续区间组合
            if non_trading_days:
                # 打印识别到的非交易日期总数，便于调试
                print(f"识别出 {len(non_trading_days)} 个非交易日，包括周末和节假日(如春节、国庆等)")
                
                # 对于连续的非交易日（如春节假期），将它们分组处理
                non_trading_days = sorted(list(non_trading_days))
                date_ranges = []
                range_start = None
                
                for i, day in enumerate(non_trading_days):
                    # 如果是该区间的第一个日期，或与前一个日期不连续
                    if range_start is None or (day - non_trading_days[i-1]).days > 1:
                        if range_start is not None:
                            date_ranges.append((range_start, non_trading_days[i-1]))
                        range_start = day
                    
                    # 如果是最后一个日期
                    if i == len(non_trading_days) - 1:
                        date_ranges.append((range_start, day))
                
                # 添加到breaks中
                for start, end in date_ranges:
                    if start.weekday() >= 5 and end.weekday() >= 5:
                        # 如果起止日期都是周末，就跳过，因为我们已经有了周末的break
                        continue
                    
                    if (end - start).days > 0:  # 确保区间有效
                        breaks.append(dict(values=[start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')]))
                
                # 应用到所有子图的X轴
                fig.update_xaxes(rangebreaks=breaks, row=1, col=1)
                fig.update_xaxes(rangebreaks=breaks, row=2, col=1)
                fig.update_xaxes(rangebreaks=breaks, row=3, col=1)
                fig.update_xaxes(rangebreaks=breaks, row=4, col=1)
        
        # 更新坐标轴标题
        fig.update_yaxes(title_text="价格", row=1, col=1)
        fig.update_yaxes(title_text="成交额(亿元)", row=2, col=1)
        fig.update_yaxes(title_text="波动比率", row=3, col=1)
        fig.update_yaxes(title_text="资金流向(亿元)", row=4, col=1)
        fig.update_xaxes(title_text="日期", row=4, col=1)

        # 添加波动比率的注释
        fig.add_annotation(
            x=data['date'].iloc[-1],
            y=0.25,
            text="强势区间",
            showarrow=False,
            xanchor="right",
            yanchor="bottom",
            row=3, col=1,
            font=dict(size=10, color="red")
        )
        fig.add_annotation(
            x=data['date'].iloc[-1],
            y=-0.25,
            text="弱势区间",
            showarrow=False,
            xanchor="right",
            yanchor="top",
            row=3, col=1,
            font=dict(size=10, color="green")
        )

        return fig
    except Exception as e:
        print(f"创建图表时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 返回一个空图表并显示错误信息
        fig = go.Figure()
        fig.update_layout(title=f"创建图表时出错: {str(e)}")
        return fig

# 创建Gradio界面
def create_gradio_interface():
    """创建Gradio界面"""
    with gr.Blocks(title="股票资金流向分析工具") as demo:
        gr.Markdown("# 股票资金流向分析工具")
        gr.Markdown("输入股票代码(如: 000001.SZ, 600519.SH)，分析其资金流向情况")
        
        with gr.Row():
            stock_input = gr.Textbox(label="股票代码", placeholder="输入格式如: 000001.SZ", value="000001.SZ")
            ktype_input = gr.Radio(
                label="数据源周期", choices=["1d", "1m", "5m", "60m"], value="1m", interactive=True
            )
            submit_btn = gr.Button("分析", variant="primary", size="sm")
        
        with gr.Row():
            with gr.Column():
                df_output = gr.DataFrame(label="资金流向数据", 
                            value=pd.DataFrame(columns=["date", "open", "close", "high", "low", "money", 
                                        "净资金流向", "波动比率"]))
                # 移除不兼容的precision参数
            
        with gr.Row():
            plot_output = gr.Plot(label="K线图与资金流向")
        
        submit_btn.click(
            fn=analyze_stock_capital_flow,
            inputs=[stock_input, ktype_input],
            outputs=[df_output, plot_output]
        )
    
    return demo

def main():
    # 创建并启动Gradio应用
    demo = create_gradio_interface()
    demo.launch(share=False)

if __name__ == "__main__":
    main()

