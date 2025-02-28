import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from layouts import home_layout, finance_layout, kline_layout, menu_layout  # 导入布局

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("财务查询", href="/finance")),
            dbc.NavItem(dbc.NavLink("K线查询", href="/kline")),
            dbc.NavItem(dbc.NavLink("菜单", href="/menu")),  # 新增菜单项
        ],
        brand="股票看板",
        brand_href="/",
        color="primary",
        dark=True,
    ),
    html.Div(id='page-content')
])

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/finance':
        return finance_layout
    elif pathname == '/kline':
        return kline_layout
    elif pathname == '/menu':
        return menu_layout  # 新增菜单布局
    else:
        return home_layout

if __name__ == '__main__':
    app.run_server(debug=True)
