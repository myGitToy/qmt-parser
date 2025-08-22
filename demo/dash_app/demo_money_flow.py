"""
使用dash展示资金流向图
模块界面介绍：
1. 数据输入：
    1.1 证券代码
    1.2 起始日期
    1.3 结束日期
    1.4 k线类型（1分钟线，5分钟线，60分钟线，日线）
    1.5 数据源 1分钟线使用akshare，日线数据使用tushare
2. 数据输出：
    2.1 数据表格 DataTable
    2.2 数据图表
        2.2.1 K线图 中国股市样式 去除所有非交易日期，K线图需要连续展示
        2.2.2 附图叠加 成交量和资金流向图
3. 核心模块：
    3.1 基于1分钟线资金流向规则：
        本K线收盘价-前收=资金流入或者流出
"""

import dash
from dash import dcc, html, dash_table, Input, Output, State, callback
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import akshare as ak
import tushare as ts
import os

# 配置 tushare token
# 请替换为您自己的 token
ts.set_token(os.environ.get('TUSHARE_TOKEN', ''))
pro = ts.pro_api()

# 初始化 Dash 应用
app = dash.Dash(__name__, title="资金流向分析")

# 应用布局
app.layout = html.Div([
    html.H1("股票资金流向分析", style={'textAlign': 'center'}),
    
    # 第一行：输入参数
    html.Div([
        # 股票代码输入
        html.Div([
            html.Label("证券代码:"),
            dcc.Input(
                id='stock-code',
                type='text',
                placeholder='例如：601318.SH 或 000001.SZ',
                value='601318.SH',
                style={'width': '100%'}
            ),
        ], style={'width': '15%', 'display': 'inline-block', 'paddingRight': '15px'}),
        
        # 开始日期选择
        html.Div([
            html.Label("起始日期:"),
            dcc.DatePickerSingle(
                id='start-date',
                date=datetime.now().date() - timedelta(days=30),
                display_format='YYYY-MM-DD'
            ),
        ], style={'width': '20%', 'display': 'inline-block', 'paddingRight': '15px'}),
        
        # 结束日期选择
        html.Div([
            html.Label("结束日期:"),
            dcc.DatePickerSingle(
                id='end-date',
                date=datetime.now().date(),
                display_format='YYYY-MM-DD'
            ),
        ], style={'width': '20%', 'display': 'inline-block', 'paddingRight': '15px'}),
        
        # K线类型选择
        html.Div([
            html.Label("K线类型:"),
            dcc.Dropdown(
                id='kline-type',
                options=[
                    {'label': '1分钟线', 'value': '1m'},
                    {'label': '5分钟线', 'value': '5m'},
                    {'label': '60分钟线', 'value': '60m'},
                    {'label': '日线', 'value': '1d'}
                ],
                value='daily'
            ),
        ], style={'width': '20%', 'display': 'inline-block', 'paddingRight': '15px'}),
        
        # 提交按钮
        html.Div([
            html.Button('获取数据', id='submit-button', n_clicks=0, 
                       style={'width': '100%', 'marginTop': '23px', 'height': '35px'})
        ], style={'width': '10%', 'display': 'inline-block'}),
    ], style={'margin': '20px'}),
    
    # 加载指示器
    dcc.Loading(
        id="loading",
        type="circle",
        children=[
            # 数据表格
            html.Div([
                html.H3("数据表格"),
                dash_table.DataTable(
                    id='stock-data-table',
                    page_size=10,
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'center',
                        'fontSize': '12px',
                        'fontFamily': 'Arial',
                    },
                    style_header={
                        'fontWeight': 'bold',
                        'backgroundColor': 'rgb(230, 230, 230)',
                    }
                ),
            ], style={'margin': '20px'}),
            
            # 图表展示
            html.Div([
                html.H3("K线图和资金流向"),
                dcc.Graph(id='kline-chart', style={'height': '600px'})
            ], style={'margin': '20px'}),
        ]
    ),
])

# 计算资金流向
def calculate_money_flow(df):
    df = df.copy()
    # 计算价格变化
    df['price_change'] = df['close'].diff()
    # 根据价格变化和成交量计算资金流向
    df['money_flow'] = df['price_change'] * df['volume']
    # 累计资金流向
    df['cumulative_flow'] = df['money_flow'].cumsum()
    return df

# 获取股票数据
def get_stock_data(code, start_date, end_date, kline_type):
    # 转换股票代码格式
    if code.startswith('6'):
        formatted_code = f"{code}.SH"
    else:
        formatted_code = f"{code}.SZ"
    
    try:
        # 根据 K 线类型选择不同的数据源和接口
        if kline_type == 'daily':
            # 使用 tushare 获取日线数据
            df = pro.daily(ts_code=formatted_code, start_date=start_date.replace('-', ''), 
                          end_date=end_date.replace('-', ''))
            # 调整列名和排序
            df = df.rename(columns={
                'trade_date': 'date', 
                'open': 'open', 
                'high': 'high', 
                'low': 'low', 
                'close': 'close', 
                'vol': 'volume'
            })
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
        else:
            # 使用 akshare 获取分钟线数据
            # akshare 的股票代码格式需要调整
            if formatted_code.endswith('.SH'):
                ak_code = f"sh{code}"
            else:
                ak_code = f"sz{code}"
            
            # 根据不同的分钟线类型调用不同的函数
            if kline_type == '1min':
                df = ak.stock_zh_a_minute(symbol=ak_code, period='1', adjust='qfq')
            elif kline_type == '5min':
                df = ak.stock_zh_a_minute(symbol=ak_code, period='5', adjust='qfq')
            elif kline_type == '60min':
                df = ak.stock_zh_a_minute(symbol=ak_code, period='60', adjust='qfq')
            
            # 调整列名
            df = df.rename(columns={
                'datetime': 'date', 
                'open': 'open', 
                'high': 'high', 
                'low': 'low', 
                'close': 'close', 
                'volume': 'volume'
            })
        
        # 按日期排序
        df = df.sort_values('date')
        # 计算资金流向
        df = calculate_money_flow(df)
        return df
    except Exception as e:
        print(f"获取数据出错: {str(e)}")
        return pd.DataFrame()

# 更新图表和表格的回调
@app.callback(
    [Output('stock-data-table', 'data'),
     Output('stock-data-table', 'columns'),
     Output('kline-chart', 'figure')],
    [Input('submit-button', 'n_clicks')],
    [State('stock-code', 'value'),
     State('start-date', 'date'),
     State('end-date', 'date'),
     State('kline-type', 'value')]
)
def update_data(n_clicks, stock_code, start_date, end_date, kline_type):
    if n_clicks > 0 and stock_code:
        # 获取股票数据
        df = get_stock_data(stock_code, start_date, end_date, kline_type)
        
        if df.empty:
            return [], [], go.Figure()
        
        # 准备数据表格
        display_columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'money_flow']
        table_data = df[display_columns].to_dict('records')
        table_columns = [{'name': col.capitalize(), 'id': col} for col in display_columns]
        
        # 创建 K 线图
        fig = make_subplots(
            rows=3, 
            cols=1, 
            shared_xaxes=True,
            vertical_spacing=0.02,
            row_heights=[0.5, 0.25, 0.25],
            subplot_titles=('K线图', '成交量', '资金流向')
        )
        
        # K线图
        fig.add_trace(
            go.Candlestick(
                x=df['date'],
                open=df['open'], 
                high=df['high'],
                low=df['low'], 
                close=df['close'],
                increasing_line_color='red', 
                decreasing_line_color='green',
                name='K线'
            ),
            row=1, col=1
        )
        
        # 成交量图
        colors = ['red' if c >= o else 'green' for o, c in zip(df['open'], df['close'])]
        fig.add_trace(
            go.Bar(
                x=df['date'], 
                y=df['volume'],
                marker_color=colors,
                name='成交量'
            ),
            row=2, col=1
        )
        
        # 资金流向图
        fig.add_trace(
            go.Scatter(
                x=df['date'], 
                y=df['cumulative_flow'],
                line=dict(color='blue', width=2),
                name='累计资金流向'
            ),
            row=3, col=1
        )
        
        # 更新布局
        fig.update_layout(
            title=f'{stock_code} 资金流向分析',
            xaxis_rangeslider_visible=False,
            height=800,
            showlegend=False,
            template='plotly_white'
        )
        
        # 设置 x 轴格式
        fig.update_xaxes(
            rangebreaks=[
                dict(bounds=["sat", "mon"]),  # 隐藏周末
                dict(bounds=[16, 9.5], pattern="hour"),  # 隐藏非交易时间
            ],
            row=1, col=1
        )
        
        # 设置 Y 轴格式
        fig.update_yaxes(title_text="价格", row=1, col=1)
        fig.update_yaxes(title_text="成交量", row=2, col=1)
        fig.update_yaxes(title_text="资金流向", row=3, col=1)
        
        return table_data, table_columns, fig
    
    return [], [], go.Figure()

# 运行服务器
if __name__ == '__main__':
    app.run(debug=True, port=8051)