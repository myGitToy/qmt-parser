import dash_core_components as dcc
import dash_html_components as html

home_layout = html.Div([
    html.H1("欢迎使用股票看板"),
    html.P("请选择上方的功能进行查询。")
])

finance_layout = html.Div([
    html.H1("财务查询"),
    dcc.Input(id='stock-code', type='text', placeholder='输入股票代码'),
    dcc.DatePickerRange(
        id='date-picker-range',
        start_date_placeholder_text='开始日期',
        end_date_placeholder_text='结束日期'
    ),
    html.Button('查询', id='submit-button', n_clicks=0),
    html.Div(id='finance-output')
])

kline_layout = html.Div([
    html.H1("K线查询"),
    dcc.Input(id='stock-code-kline', type='text', placeholder='输入股票代码'),
    dcc.DatePickerRange(
        id='date-picker-range-kline',
        start_date_placeholder_text='开始日期',
        end_date_placeholder_text='结束日期'
    ),
    html.Button('查询', id='submit-button-kline', n_clicks=0),
    html.Div(id='kline-output')
])

menu_layout = html.Div([
    html.H1("菜单"),
    html.P("这是一个新的菜单页面。")
])
