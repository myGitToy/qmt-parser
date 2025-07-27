from dash.dependencies import Input, Output, State
import dash_html_components as html
from app import app

@app.callback(
    Output('finance-output', 'children'),
    [Input('submit-button', 'n_clicks')],
    [State('stock-code', 'value'),
     State('date-picker-range', 'start_date'),
     State('date-picker-range', 'end_date')]
)
def update_finance_output(n_clicks, stock_code, start_date, end_date):
    if n_clicks > 0:
        # 在这里添加查询逻辑
        return html.Div([
            html.P(f"查询股票代码: {stock_code}"),
            html.P(f"查询日期范围: {start_date} 到 {end_date}")
        ])
    return html.Div()

@app.callback(
    Output('kline-output', 'children'),
    [Input('submit-button-kline', 'n_clicks')],
    [State('stock-code-kline', 'value'),
     State('date-picker-range-kline', 'start_date'),
     State('date-picker-range-kline', 'end_date')]
)
def update_kline_output(n_clicks, stock_code, start_date, end_date):
    if n_clicks > 0:
        # 在这里添加查询逻辑
        return html.Div([
            html.P(f"查询股票代码: {stock_code}"),
            html.P(f"查询日期范围: {start_date} 到 {end_date}")
        ])
    return html.Div()
