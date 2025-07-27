"""
彭博终端风格金融数据平台
使用Streamlit构建的最小化原型
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.subplots as sp
from plotly.subplots import make_subplots
import sys
from pathlib import Path
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 添加项目根目录到路径
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

try:
    from apt.vendor.tspro.data import data as ts_data
    from apt.vendor.akshare.data import data as ak_data
    DATA_SOURCE_AVAILABLE = True
except ImportError:
    DATA_SOURCE_AVAILABLE = False

# 页面配置
st.set_page_config(
    page_title="Bloomberg Terminal Demo",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式，模仿彭博终端的黑色主题
st.markdown("""
<style>
    .stApp {
        background-color: #1a1a1a;
        color: #ffffff;
    }
    
    .css-1d391kg {
        background-color: #1a1a1a;
    }
    
    .css-12oz5g7 {
        background-color: #2d2d2d;
    }
    
    .stSelectbox > div > div {
        background-color: #2d2d2d;
        color: #ffffff;
    }
    
    .stMetric {
        background-color: #2d2d2d;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #00d4ff;
    }
    
    .bloomberg-header {
        background: linear-gradient(90deg, #ff6600 0%, #ff8c00 100%);
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    
    .market-widget {
        background-color: #2d2d2d;
        padding: 15px;
        border-radius: 8px;
        margin: 5px 0;
        border-left: 3px solid #00ff88;
    }
    
    .price-up {
        color: #00ff88;
    }
    
    .price-down {
        color: #ff4444;
    }
</style>
""", unsafe_allow_html=True)

def generate_sample_data(symbol, days=30):
    """生成示例股票数据"""
    dates = pd.date_range(start=datetime.now() - timedelta(days=days), 
                         end=datetime.now(), freq='D')
    
    # 生成模拟股票价格数据
    np.random.seed(42)
    price = 100
    prices = []
    volumes = []
    
    for _ in range(len(dates)):
        change = np.random.normal(0, 2)
        price = max(price + change, 10)  # 确保价格不低于10
        prices.append(price)
        volumes.append(np.random.randint(1000000, 10000000))
    
    df = pd.DataFrame({
        'date': dates,
        'close': prices,
        'open': [p * (1 + np.random.uniform(-0.02, 0.02)) for p in prices],
        'high': [p * (1 + np.random.uniform(0, 0.05)) for p in prices],
        'low': [p * (1 + np.random.uniform(-0.05, 0)) for p in prices],
        'volume': volumes
    })
    
    return df

def get_real_data(symbol, start_date, end_date):
    """获取真实股票数据"""
    if not DATA_SOURCE_AVAILABLE:
        return generate_sample_data(symbol)
    
    try:
        ts = ts_data()
        ts.start_date = start_date
        ts.end_date = end_date
        ts.code = symbol
        data = ts.get_k_data()
        return data
    except:
        return generate_sample_data(symbol)

def create_candlestick_chart(df, title):
    """创建K线图"""
    fig = go.Figure(data=go.Candlestick(
        x=df['date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name="K线"
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="时间",
        yaxis_title="价格",
        template="plotly_dark",
        height=400,
        paper_bgcolor='#1a1a1a',
        plot_bgcolor='#1a1a1a',
        font=dict(color='white')
    )
    
    return fig

def create_volume_chart(df):
    """创建成交量图"""
    fig = go.Figure(data=go.Bar(
        x=df['date'],
        y=df['volume'],
        name="成交量",
        marker_color='#00d4ff'
    ))
    
    fig.update_layout(
        title="成交量",
        xaxis_title="时间",
        yaxis_title="成交量",
        template="plotly_dark",
        height=200,
        paper_bgcolor='#1a1a1a',
        plot_bgcolor='#1a1a1a',
        font=dict(color='white')
    )
    
    return fig

def main():
    # 标题头部
    st.markdown("""
    <div class="bloomberg-header">
        <h1 style="margin:0; color:white;">🏦 Bloomberg Terminal Demo</h1>
        <p style="margin:5px 0 0 0; color:white;">专业金融数据终端演示平台</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 侧边栏
    st.sidebar.title("📊 终端控制面板")
    
    # 股票代码选择
    popular_stocks = [
        "600519.sh",  # 贵州茅台
        "000858.sz",  # 五 粮 液
        "000001.sz",  # 平安银行
        "600036.sh",  # 招商银行
        "600000.sh",  # 浦发银行
    ]
    
    selected_stock = st.sidebar.selectbox(
        "选择股票代码",
        popular_stocks,
        help="选择要分析的股票代码"
    )
    
    # 时间范围选择
    time_range = st.sidebar.selectbox(
        "时间范围",
        ["1个月", "3个月", "6个月", "1年"],
        index=1
    )
    
    # 计算时间范围
    time_mapping = {
        "1个月": 30,
        "3个月": 90, 
        "6个月": 180,
        "1年": 365
    }
    days = time_mapping[time_range]
    
    start_date = datetime.now() - timedelta(days=days)
    end_date = datetime.now()
    
    # 获取数据
    with st.spinner('正在获取市场数据...'):
        df = get_real_data(selected_stock, start_date, end_date)
    
    if df.empty:
        st.error("无法获取数据，请检查网络连接或数据源")
        return
    
    # 主要指标面板
    col1, col2, col3, col4 = st.columns(4)
    
    current_price = df['close'].iloc[-1]
    prev_price = df['close'].iloc[-2] if len(df) > 1 else current_price
    price_change = current_price - prev_price
    price_change_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0
    
    with col1:
        st.metric(
            label="💰 当前价格",
            value=f"¥{current_price:.2f}",
            delta=f"{price_change:+.2f} ({price_change_pct:+.2f}%)"
        )
    
    with col2:
        st.metric(
            label="📈 最高价",
            value=f"¥{df['high'].max():.2f}",
            delta=f"近{time_range}"
        )
    
    with col3:
        st.metric(
            label="📉 最低价", 
            value=f"¥{df['low'].min():.2f}",
            delta=f"近{time_range}"
        )
    
    with col4:
        avg_volume = df['volume'].mean()
        st.metric(
            label="📊 平均成交量",
            value=f"{avg_volume/10000:.0f}万",
            delta="日均"
        )
    
    # 图表区域
    st.markdown("---")
    
    # K线图
    st.subheader(f"📈 {selected_stock} K线图")
    candlestick_fig = create_candlestick_chart(df, f"{selected_stock} 股价走势")
    st.plotly_chart(candlestick_fig, use_container_width=True)
    
    # 成交量图
    st.subheader("📊 成交量分析")
    volume_fig = create_volume_chart(df)
    st.plotly_chart(volume_fig, use_container_width=True)
    
    # 技术分析面板
    st.markdown("---")
    st.subheader("🔬 技术分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 移动平均线
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA20'] = df['close'].rolling(window=20).mean()
        
        ma_fig = go.Figure()
        ma_fig.add_trace(go.Scatter(x=df['date'], y=df['close'], name='收盘价', line=dict(color='white')))
        ma_fig.add_trace(go.Scatter(x=df['date'], y=df['MA5'], name='MA5', line=dict(color='yellow')))
        ma_fig.add_trace(go.Scatter(x=df['date'], y=df['MA20'], name='MA20', line=dict(color='cyan')))
        
        ma_fig.update_layout(
            title="移动平均线",
            template="plotly_dark",
            height=350,
            paper_bgcolor='#1a1a1a',
            plot_bgcolor='#1a1a1a',
            font=dict(color='white')
        )
        
        st.plotly_chart(ma_fig, use_container_width=True)
    
    with col2:
        # RSI指标（简化版）
        def calculate_rsi(prices, period=14):
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        
        df['RSI'] = calculate_rsi(df['close'])
        
        rsi_fig = go.Figure()
        rsi_fig.add_trace(go.Scatter(x=df['date'], y=df['RSI'], name='RSI', line=dict(color='orange')))
        rsi_fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="超买线")
        rsi_fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="超卖线")
        
        rsi_fig.update_layout(
            title="RSI相对强弱指数",
            yaxis=dict(range=[0, 100]),
            template="plotly_dark",
            height=350,
            paper_bgcolor='#1a1a1a',
            plot_bgcolor='#1a1a1a',
            font=dict(color='white')
        )
        
        st.plotly_chart(rsi_fig, use_container_width=True)
    
    # 数据表格
    st.markdown("---")
    st.subheader("📋 历史数据")
    
    # 格式化数据显示
    display_df = df.copy()
    display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
    display_df = display_df.round(2)
    
    st.dataframe(
        display_df.tail(10),
        use_container_width=True,
        height=300
    )
    
    # 底部信息
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #888888; padding: 20px;">
        💡 Bloomberg Terminal Demo | 数据更新时间: {} | 
        数据来源: TuShare Pro / AKShare
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
