import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from dash.dependencies import MATCH

# Enable o4-mini Preview for all clients
#dash._dash_renderer._default_renderer.config.o4_mini = True

"""
DASH表单组件的菜单显示
主页面包含左侧列表型菜单，点击菜单项可以在主页面中显示不同的内容。
一级菜单：行情数据、财务数据、资金流向、数据分析、数据挖掘、数据校验、数据迁移
二级菜单按需添加：
    数据校验的二级菜单：
        1.tspro日线校验
        2.akshare_1m校验
        3.akshare_5m校验
        4.akshare_60m校验
    数据迁移的二级菜单：
        1.K线数据迁移
        2.资金流向迁移
"""


# 初始化Dash应用
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# 定义侧边栏样式
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
    "overflow-y": "auto"
}

# 定义标题栏样式
HEADER_STYLE = {
    "background-color": "#343a40",
    "color": "white",
    "padding": "1rem",
    "text-align": "center",
    "font-size": "1.5rem",
}

# 定义页脚样式
FOOTER_STYLE = {
    "background-color": "#343a40",
    "color": "white",
    "padding": "0.5rem",
    "text-align": "center",
    "position": "fixed",
    "bottom": 0,
    "width": "100%",
}

# 定义主要内容区域样式（优化间距和背景色）
CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
    "min-height": "calc(100vh - 6rem)",  # 考虑标题栏和页脚的高度
}

# 创建侧边栏菜单
sidebar = html.Div(
    [
        html.H2("菜单", className="display-6"),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink("行情数据", href="/market-data", id="market-data-link", active="exact"),
                dbc.NavLink("财务数据", href="/financial-data", id="financial-data-link", active="exact"),
                dbc.NavLink("资金流向", href="/capital-flow", id="capital-flow-link", active="exact"),
                dbc.NavLink("数据分析", href="/data-analysis", id="data-analysis-link", active="exact"),
                dbc.NavLink("数据挖掘", href="/data-mining", id="data-mining-link", active="exact"),
                dbc.NavLink(
                    "数据校验", 
                    href="#", 
                    id="data-validation-link", 
                    active="exact", 
                    n_clicks=0
                ),
                dbc.Collapse(
                    [
                        dbc.NavLink("K线校验", href="/validation-kdata-daily", id="validation-kdata-daily-link", className="ms-3"),
                        dbc.NavLink("tspro日线校验", href="/validation-tspro-daily", id="validation-tspro-daily-link", className="ms-3"),
                        dbc.NavLink("akshare_1m校验", href="/validation-akshare-1m", id="validation-akshare-1m-link", className="ms-3"),
                        dbc.NavLink("akshare_5m校验", href="/validation-akshare-5m", id="validation-akshare-5m-link", className="ms-3"),
                        dbc.NavLink("akshare_60m校验", href="/validation-akshare-60m", id="validation-akshare-60m-link", className="ms-3"),
                    ],
                    id="submenu-data-validation",
                    is_open=False,
                ),
                dbc.NavLink(
                    "数据迁移", 
                    href="#", 
                    id="data-migration-link", 
                    active="exact", 
                    n_clicks=0
                ),
                dbc.Collapse(
                    [
                        dbc.NavLink("K线数据迁移", href="/migration-kdata", id="migration-kdata-link", className="ms-3"),
                        dbc.NavLink("资金流向迁移", href="/migration-capital-flow", id="migration-capital-flow-link", className="ms-3"),
                    ],
                    id="submenu-data-migration",
                    is_open=False,
                ),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

# 创建标题栏
header = html.Div("量化交易测试版", style=HEADER_STYLE)

# 创建内容区域
content = html.Div(id="page-content", style=CONTENT_STYLE)

# 创建页脚
footer = html.Div("© 2025 Hui Qiao", style=FOOTER_STYLE)

# 页面布局
app.layout = html.Div(
    [
        header,
        dcc.Location(id="url"),
        sidebar,
        content,
        footer,
    ]
)

# 创建回调函数，用于处理菜单点击并显示相应内容
@callback(
    Output("page-content", "children"),
    [Input("url", "pathname")]
)
def render_page_content(pathname):
    if pathname == "/market-data":
        return html.H1("行情数据")
    elif pathname == "/financial-data":
        return html.H1("财务数据")
    elif pathname == "/capital-flow":
        return html.H1("资金流向")
    elif pathname == "/data-analysis":
        return html.H1("数据分析")
    elif pathname == "/data-mining":
        return html.H1("数据挖掘")
    elif pathname == "/data-validation":
        return html.H1("数据校验")
    elif pathname == "/validation-tspro-daily":
        return html.H1("tspro日线校验")
    elif pathname == "/validation-akshare-1m":
        return html.H1("akshare_1m校验")
    elif pathname == "/validation-akshare-5m":
        return html.H1("akshare_5m校验")
    elif pathname == "/validation-akshare-60m":
        return html.H1("akshare_60m校验")
    elif pathname == "/validation-kdata-daily":
        from pages.validation_kdata_daily import layout
        return layout
    elif pathname == "/migration-kdata":
        return html.H1("K线数据迁移")
    elif pathname == "/migration-capital-flow":
        return html.H1("资金流向迁移")
    else:
        # 默认显示
        return html.H1("请从左侧菜单选择功能")

# 显示/隐藏子菜单
@callback(
    Output("submenu-data-validation", "is_open"),
    [Input("data-validation-link", "n_clicks")],
    [State("submenu-data-validation", "is_open")]
)
def toggle_validation_submenu(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

@callback(
    Output("submenu-data-migration", "is_open"),
    [Input("data-migration-link", "n_clicks")],
    [State("submenu-data-migration", "is_open")]
)
def toggle_migration_submenu(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

# 运行应用
if __name__ == "__main__":
    app.run_server(debug=True)
