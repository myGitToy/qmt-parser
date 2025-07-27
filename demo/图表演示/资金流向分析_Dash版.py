"""
本模块用于分析个股资金流向，Dash版本:
1. 基于每只股票的OHLC和成交金额计算资金流入/流出
2. 可视化展示K线、均线、成交量、波动比率和资金流向
3. 提供交互式界面，支持输入股票代码进行查询
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from apt.vendor.tspro.data import data as tspro_data
from apt.vendor.akshare.data import data as ak_data
import akshare as ak
from datetime import datetime, timedelta
from tqdm import tqdm
import os

# Dash相关库
import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class CapitalFlowAnalyzer(ak_data):
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
        
        # 计算波动比率：(收盘价-前收盘价或开盘价)/(最高价-最低价)
        df['prev_close'] = df['close'].shift(1)
        df['波动比率'] = df.apply(
            lambda row: (row['close'] - (row['prev_close'] if pd.notnull(row['prev_close']) else row['open'])) / (row['high'] - row['low'])
            if (row['high'] != row['low']) else 0, axis=1
        )
        
        # 创建一个有限制的波动比率版本用于资金流向计算
        # 将波动比率限制在[-1, 1]范围内（即-100%到+100%）
        df['限制波动比率'] = df['波动比率'].apply(lambda x: max(min(x, 1), -1))
        
        # 计算资金流向：限制后的波动比率 * 成交金额
        df['净资金流向'] = df['限制波动比率'] * df['money']
        
        # 转换单位和保留小数点位数
        df['净资金流向'] = (df['净资金流向'] / 1000000).round(1)  # 转换为百万并保留1位小数
        df['波动比率'] = df['波动比率'].round(2)  # 波动比率保留2位小数
        
        # 为了保持与之前代码的一致性，还可以计算积极流入和消极流出
        df['积极流入'] = df['净资金流向'].apply(lambda x: x if x > 0 else 0)
        df['消极流出'] = df['净资金流向'].apply(lambda x: -x if x < 0 else 0)
        
        return df

def analyze_stock_capital_flow(stock_code, ktype='1d', start_date=None):
    """分析单只股票的资金流向
    
    Args:
        stock_code: 股票代码
        ktype: K线类型，可选值: '1d'(日线), '60m'(60分钟线), '5m'(5分钟线)
        start_date: 起始日期，如果没有指定，则根据K线类型自动设置
    """
    try:
        # 创建分析器实例
        analyzer = CapitalFlowAnalyzer()
        analyzer.code = stock_code.strip()  # 去除可能的空格
        
        # 根据K线类型和用户选择设置数据获取时间范围
        if start_date:
            analyzer.start_date = pd.to_datetime(start_date)  # 使用用户选择的日期
        else:
            # 默认值
            if ktype == '1d':
                analyzer.start_date = datetime(2023, 1, 1)  # 日线数据可以获取较长时间
            elif ktype == '60m':
                # 60分钟线获取近3个月数据
                analyzer.start_date = datetime.now() - timedelta(days=90)
            else:  # 5m
                # 5分钟线获取近2周数据
                analyzer.start_date = datetime.now() - timedelta(days=14)
            
        analyzer.end_date = datetime.now()  # 结束日期
        analyzer.ktype = ktype  # 设置K线周期
        
        # 获取股票数据
        analyzer.stock_data = analyzer.get_k_data()
        
        # 调试信息，检查数据是否正确获取
        print(f"获取到的数据行数: {len(analyzer.stock_data)}")
        if len(analyzer.stock_data) > 0:
            print(f"日期范围: {analyzer.stock_data['date'].min()} - {analyzer.stock_data['date'].max()}")
        else:
            print("警告：未获取到任何数据")
            return pd.DataFrame({'错误': ['未获取到任何交易数据']}), {}
        
        # 计算资金流向
        flow_data = analyzer.calculate_single_stock_flow()
        
        # 获取可视化所需数据
        result_df = flow_data[['date', 'open', 'close', 'high', 'low', 'volume', '净资金流向', '波动比率']]
        result_df = result_df.tail(60)  # 最近60个交易日，可调整
        
        # 创建图表
        fig = create_single_stock_figure(result_df, stock_code, ktype)
        
        # 返回数据和图表
        return result_df, fig
        
    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        traceback.print_exc()  # 打印详细错误堆栈
        return pd.DataFrame({'错误': [str(e)]}), {}

def create_single_stock_figure(data, stock_code, ktype='1d'):
    """创建单一股票的K线图和资金流向图"""
    # 检查数据是否有效
    if len(data) == 0:
        fig = go.Figure()
        fig.update_layout(title="没有数据可供显示")
        return fig
    
    # 确保日期格式正确
    if not pd.api.types.is_datetime64_any_dtype(data['date']):
        data['date'] = pd.to_datetime(data['date'])
    
    # 创建包含三个子图的图表，为波动比率预留单独的区域
    try:
        fig = make_subplots(rows=3, cols=1,
                           shared_xaxes=True,
                           vertical_spacing=0.05,
                           row_heights=[0.5, 0.2, 0.3])
        
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
        
        # 添加波动比率柱状图作为中间图表
        colors_ratio = ['red' if x > 0 else 'green' for x in data['波动比率']]
        fig.add_trace(
            go.Bar(
                x=data['date'],
                y=data['波动比率'],
                name='波动比率',
                marker_color=colors_ratio
            ),
            row=2, col=1
        )
        
        # 添加参考线表示±0.5和0
        fig.add_shape(
            type="line", line=dict(dash="dash", color="gray"),
            x0=data['date'].iloc[0], y0=0,
            x1=data['date'].iloc[-1], y1=0,
            row=2, col=1
        )
        fig.add_shape(
            type="line", line=dict(dash="dot", color="red", width=1),
            x0=data['date'].iloc[0], y0=0.5,
            x1=data['date'].iloc[-1], y1=0.5,
            row=2, col=1
        )
        fig.add_shape(
            type="line", line=dict(dash="dot", color="green", width=1),
            x0=data['date'].iloc[0], y0=-0.5,
            x1=data['date'].iloc[-1], y1=-0.5,
            row=2, col=1
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
            row=3, col=1
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
            row=3, col=1
        )
        
        # 处理交易日期，使K线连续
        if len(data) > 1:
            # 构建rangebreaks
            breaks = []
            
            # 根据K线类型设置不同的rangebreaks规则
            if ktype == '1d':
                # 日线图跳过周末和节假日
                # 识别所有非交易日
                data_dates = set(data['date'].dt.date)
                
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
                
                # 跳过周末
                breaks.append(dict(bounds=["sat", "mon"]))
                
                # 将非交易日日期按连续区间组合
                if non_trading_days:
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
            
            else:  # 60m或5m分钟线图
                # 1. 跳过夜间非交易时间 (15:00-次日9:30)
                breaks.append(dict(bounds=[15, 9.5], pattern="hour"))  # 每天15:00后到次日9:30前跳过
                
                # 2. 跳过中午休市时间 (11:30-13:00)
                breaks.append(dict(bounds=[11.5, 13], pattern="hour"))  # 每天11:30-13:00跳过
                
                # 3. 跳过周末
                breaks.append(dict(bounds=["sat", "mon"]))
            
            # 应用到所有三个子图的X轴
            fig.update_xaxes(rangebreaks=breaks, row=1, col=1)
            fig.update_xaxes(rangebreaks=breaks, row=2, col=1)
            fig.update_xaxes(rangebreaks=breaks, row=3, col=1)
        
        # 更新布局
        fig.update_layout(
            title=f'{stock_code} 股票资金流向与波动比率分析',
            height=800,  # 高度设置
            template="plotly_white",
            xaxis_rangeslider_visible=False,
            margin=dict(l=50, r=50, t=80, b=50),
        )
        
        # 更新坐标轴标题
        fig.update_yaxes(title_text="价格", row=1, col=1)
        fig.update_yaxes(title_text="波动比率", row=2, col=1)
        fig.update_yaxes(title_text="资金流向(亿元)", row=3, col=1)
        fig.update_xaxes(title_text="日期", row=3, col=1)
        
        # 添加波动比率的注释
        fig.add_annotation(
            x=data['date'].iloc[-1],
            y=0.6,
            text="强势区间",
            showarrow=False,
            xanchor="right",
            yanchor="bottom",
            row=2, col=1,
            font=dict(size=10, color="red")
        )
        fig.add_annotation(
            x=data['date'].iloc[-1],
            y=-0.6,
            text="弱势区间",
            showarrow=False,
            xanchor="right",
            yanchor="top",
            row=2, col=1,
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

# 创建Dash应用
app = dash.Dash(__name__)
server = app.server

# 应用布局
app.layout = html.Div([
    # 标题和说明
    html.Div([
        html.H1("股票资金流向分析工具", style={'textAlign': 'center'}),
        html.P("输入股票代码(如: 000001.SZ, 600519.SH)，分析其资金流向情况",
               style={'textAlign': 'center', 'fontSize': '1.2em'}),
    ], style={'marginBottom': 20}),
    
    # 输入区域
    html.Div([
        html.Div([
            html.Label("股票代码:", style={'marginRight': '5px'}),
            dcc.Input(id='stock-input', value='000001.SZ', type='text',
                      style={'width': '150px', 'marginRight': '20px'}),
            
            html.Label("K线周期:", style={'marginRight': '5px'}),
            dcc.Dropdown(
                id='ktype-dropdown',
                options=[
                    {'label': '日线', 'value': '1d'},
                    {'label': '60分钟线', 'value': '60m'},
                    {'label': '5分钟线', 'value': '5m'}
                ],
                value='1d',
                style={'width': '150px', 'marginRight': '10px'}
            ),
            
            html.Label("起始日期:", style={'marginRight': '5px'}),
            dcc.DatePickerSingle(
                id='start-date-picker',
                date=datetime(2023, 1, 1).strftime('%Y-%m-%d'),
                style={'marginRight': '20px'}
            ),
            
            html.Button('分析', id='submit-button', n_clicks=0,
                       style={'backgroundColor': '#4CAF50', 'color': 'white',
                              'border': 'none', 'padding': '10px 20px'})
        ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'})
    ], style={'marginBottom': 20}),
    
    # 加载指示器
    dcc.Loading(
        id="loading",
        type="circle",
        children=[
            # 图表区域
            html.Div([
                dcc.Graph(id='stock-chart', style={'height': '800px'}),
            ], style={'marginBottom': 20}),
            
            # 数据表格
            html.Div([
                html.H3("资金流向数据", style={'textAlign': 'center'}),
                dash_table.DataTable(
                    id='stock-data-table',
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'center',
                        'minWidth': '80px', 'width': '80px', 'maxWidth': '120px',
                        'whiteSpace': 'normal'
                    },
                    style_header={
                        'backgroundColor': '#f8f9fa',
                        'fontWeight': 'bold'
                    },
                    style_data_conditional=[
                        {
                            'if': {'column_id': '净资金流向', 'filter_query': '{净资金流向} > 0'},
                            'backgroundColor': 'rgba(255, 0, 0, 0.1)',
                            'color': 'red'
                        },
                        {
                            'if': {'column_id': '净资金流向', 'filter_query': '{净资金流向} < 0'},
                            'backgroundColor': 'rgba(0, 255, 0, 0.1)',
                            'color': 'green'
                        }
                    ],
                    page_size=15
                )
            ])
        ]
    )
])

# 回调函数
@app.callback(
    [Output('stock-chart', 'figure'), 
     Output('stock-data-table', 'data'),
     Output('stock-data-table', 'columns')],
    [Input('submit-button', 'n_clicks')],
    [State('stock-input', 'value'),
     State('ktype-dropdown', 'value'),
     State('start-date-picker', 'date')]
)
def update_output(n_clicks, stock_code, ktype, start_date):
    if n_clicks > 0 and stock_code:
        # 将日期字符串转换为datetime对象
        start_date = datetime.strptime(start_date.split('T')[0], '%Y-%m-%d') if start_date else None
        
        # 获取数据和创建图表
        result_df, fig = analyze_stock_capital_flow(stock_code, ktype, start_date)
        
        # 准备表格数据
        if '错误' in result_df.columns:
            data = result_df.to_dict('records')
            columns = [{"name": i, "id": i} for i in result_df.columns]
            return {}, data, columns  # 返回空图表和错误信息
            
        # 格式化日期列以便在表格中更好地显示
        if ktype != '1d':
            result_df['date'] = result_df['date'].dt.strftime('%Y-%m-%d %H:%M')
        else:
            result_df['date'] = result_df['date'].dt.strftime('%Y-%m-%d')
        
        # 准备数据表格
        data = result_df.to_dict('records')
        columns = [{"name": i, "id": i} for i in result_df.columns]
        
        return fig, data, columns
    
    # 初始状态或无效输入
    return {}, [], []

# 运行应用
if __name__ == '__main__':
    app.run_server(debug=True, port=8051)
