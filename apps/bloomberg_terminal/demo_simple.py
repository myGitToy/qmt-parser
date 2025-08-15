"""
彭博终端风格金融数据平台 - 简化版本
不依赖外部数据源的演示版本
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 页面配置
st.set_page_config(
    page_title="Bloomberg Terminal Demo",
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 彭博终端风格CSS
st.markdown("""
<style>
    .stApp {
        background-color: #1a1a1a;
        color: #ffffff;
    }
    
    .css-1d391kg {
        background-color: #1a1a1a;
    }
    
    .bloomberg-header {
        background: linear-gradient(90deg, #ff6600 0%, #ff8c00 100%);
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
    }
    
    .metric-card {
        background-color: #2d2d2d;
        padding: 15px;
        border-radius: 8px;
        margin: 5px 0;
        border-left: 4px solid #00d4ff;
    }
    
    .price-up { color: #00ff88; }
    .price-down { color: #ff4444; }
    .price-neutral { color: #ffffff; }
</style>
""", unsafe_allow_html=True)

def generate_stock_data(symbol, days=30):
    """生成模拟股票数据"""
    dates = pd.date_range(start=datetime.now() - timedelta(days=days), 
                         end=datetime.now(), freq='D')
    
    # 设置随机种子以确保一致性
    np.random.seed(hash(symbol) % 1000)
    
    # 基础价格根据股票代码设置
    base_prices = {
        "600519.sh": 1800,  # 贵州茅台
        "000858.sz": 150,   # 五粮液  
        "000001.sz": 12,    # 平安银行
        "600036.sh": 45,    # 招商银行
        "600000.sh": 8,     # 浦发银行
    }
    
    base_price = base_prices.get(symbol, 100)
    
    prices = []
    volumes = []
    price = base_price
    
    for i in range(len(dates)):
        # 添加一些趋势和随机性
        trend = np.sin(i * 0.1) * 0.02  # 周期性趋势
        change = np.random.normal(trend, 0.03)  # 随机变化
        price = max(price * (1 + change), base_price * 0.5)  # 防止价格过低
        prices.append(price)
        
        # 成交量也添加一些变化
        base_volume = 5000000
        volume_change = np.random.normal(0, 0.5)
        volume = max(base_volume * (1 + volume_change), base_volume * 0.1)
        volumes.append(int(volume))
    
    df = pd.DataFrame({
        'date': dates,
        'close': prices,
    })
    
    # 计算开盘、最高、最低价
    df['open'] = df['close'].shift(1).fillna(df['close'].iloc[0])
    df['high'] = df[['open', 'close']].max(axis=1) * (1 + np.random.uniform(0, 0.02, len(df)))
    df['low'] = df[['open', 'close']].min(axis=1) * (1 - np.random.uniform(0, 0.02, len(df)))
    df['volume'] = volumes
    
    return df

def create_candlestick_chart(df, title):
    """创建K线图"""
    fig = go.Figure(data=go.Candlestick(
        x=df['date'],
        open=df['open'],
        high=df['high'], 
        low=df['low'],
        close=df['close'],
        name="K线",
        increasing_line_color='#00ff88',
        decreasing_line_color='#ff4444'
    ))
    
    fig.update_layout(
        title=f"📈 {title}",
        xaxis_title="时间",
        yaxis_title="价格 (¥)",
        template="plotly_dark",
        height=400,
        paper_bgcolor='#1a1a1a',
        plot_bgcolor='#1a1a1a',
        font=dict(color='white', size=12),
        showlegend=False,
        xaxis=dict(gridcolor='#333333'),
        yaxis=dict(gridcolor='#333333')
    )
    
    return fig

def create_volume_chart(df):
    """创建成交量图"""
    colors = ['#00ff88' if close >= open else '#ff4444' 
              for close, open in zip(df['close'], df['open'])]
    
    fig = go.Figure(data=go.Bar(
        x=df['date'],
        y=df['volume'],
        name="成交量",
        marker_color=colors,
        opacity=0.7
    ))
    
    fig.update_layout(
        title="📊 成交量",
        xaxis_title="时间",
        yaxis_title="成交量",
        template="plotly_dark",
        height=200,
        paper_bgcolor='#1a1a1a',
        plot_bgcolor='#1a1a1a',
        font=dict(color='white', size=12),
        showlegend=False,
        xaxis=dict(gridcolor='#333333'),
        yaxis=dict(gridcolor='#333333')
    )
    
    return fig

def main():
    # 标题头部
    st.markdown("""
    <div class="bloomberg-header">
        <h1 style="margin:0; color:white; font-size:2.5em;">🏦 Bloomberg Terminal Demo</h1>
        <p style="margin:5px 0 0 0; color:white; font-size:1.2em;">专业金融数据终端演示平台</p>
        <p style="margin:5px 0 0 0; color:#cccccc; font-size:0.9em;">模拟数据仅供演示 • {} </p>
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)
    
    # 侧边栏控制面板
    st.sidebar.markdown("### 📊 终端控制面板")
    
    # 股票选择
    stock_options = {
        "600519.sh": "🍷 贵州茅台",
        "000858.sz": "🥃 五粮液", 
        "000001.sz": "🏦 平安银行",
        "600036.sh": "💳 招商银行",
        "600000.sh": "🏛️ 浦发银行"
    }
    
    selected_stock = st.sidebar.selectbox(
        "选择股票",
        list(stock_options.keys()),
        format_func=lambda x: stock_options[x],
        help="选择要分析的股票代码"
    )
    
    # 时间范围
    time_range = st.sidebar.selectbox(
        "时间范围",
        ["1个月", "3个月", "6个月", "1年"],
        index=1
    )
    
    # 显示选项
    show_ma = st.sidebar.checkbox("显示移动平均线", value=True)
    show_volume = st.sidebar.checkbox("显示成交量", value=True)
    show_rsi = st.sidebar.checkbox("显示RSI指标", value=True)
    
    # 计算天数
    time_mapping = {"1个月": 30, "3个月": 90, "6个月": 180, "1年": 365}
    days = time_mapping[time_range]
    
    # 生成数据
    with st.spinner('📊 正在加载市场数据...'):
        df = generate_stock_data(selected_stock, days)
    
    # 计算关键指标
    current_price = df['close'].iloc[-1]
    prev_price = df['close'].iloc[-2] if len(df) > 1 else current_price
    price_change = current_price - prev_price
    price_change_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0
    
    # 主要指标面板
    st.markdown("### 💰 关键指标")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="当前价格",
            value=f"¥{current_price:.2f}",
            delta=f"{price_change:+.2f} ({price_change_pct:+.2f}%)"
        )
    
    with col2:
        high_price = df['high'].max()
        st.metric(
            label=f"最高价 ({time_range})",
            value=f"¥{high_price:.2f}",
            delta=f"+{((high_price/current_price-1)*100):+.1f}%"
        )
    
    with col3:
        low_price = df['low'].min()
        st.metric(
            label=f"最低价 ({time_range})",
            value=f"¥{low_price:.2f}",
            delta=f"{((low_price/current_price-1)*100):+.1f}%"
        )
    
    with col4:
        avg_volume = df['volume'].mean()
        st.metric(
            label="平均成交量",
            value=f"{avg_volume/10000:.0f}万",
            delta="日均"
        )
    
    # 图表区域
    st.markdown("---")
    
    # K线图
    candlestick_fig = create_candlestick_chart(df, f"{stock_options[selected_stock]} 股价走势")
    
    # 添加移动平均线
    if show_ma:
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA20'] = df['close'].rolling(window=20).mean()
        
        candlestick_fig.add_trace(go.Scatter(
            x=df['date'], 
            y=df['MA5'], 
            name='MA5',
            line=dict(color='yellow', width=1),
            opacity=0.8
        ))
        
        candlestick_fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['MA20'], 
            name='MA20',
            line=dict(color='cyan', width=1),
            opacity=0.8
        ))
    
    st.plotly_chart(candlestick_fig, use_container_width=True)
    
    # 成交量图
    if show_volume:
        volume_fig = create_volume_chart(df)
        st.plotly_chart(volume_fig, use_container_width=True)
    
    # 技术分析
    if show_rsi:
        st.markdown("### 🔬 技术分析")
        
        def calculate_rsi(prices, period=14):
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        
        df['RSI'] = calculate_rsi(df['close'])
        
        rsi_fig = go.Figure()
        rsi_fig.add_trace(go.Scatter(
            x=df['date'], 
            y=df['RSI'],
            name='RSI',
            line=dict(color='orange', width=2)
        ))
        
        # 添加超买超卖线
        rsi_fig.add_hline(y=70, line_dash="dash", line_color="red", 
                         annotation_text="超买线 (70)", annotation_position="top right")
        rsi_fig.add_hline(y=30, line_dash="dash", line_color="green",
                         annotation_text="超卖线 (30)", annotation_position="bottom right")
        
        rsi_fig.update_layout(
            title="📈 RSI相对强弱指数",
            yaxis=dict(range=[0, 100], title="RSI值"),
            xaxis_title="时间",
            template="plotly_dark",
            height=300,
            paper_bgcolor='#1a1a1a',
            plot_bgcolor='#1a1a1a',
            font=dict(color='white'),
            showlegend=False,
            xaxis=dict(gridcolor='#333333'),
            yaxis=dict(gridcolor='#333333')
        )
        
        st.plotly_chart(rsi_fig, use_container_width=True)
        
        # RSI解读
        current_rsi = df['RSI'].iloc[-1]
        if current_rsi > 70:
            st.warning(f"⚠️ 当前RSI值: {current_rsi:.1f} - 股票可能处于超买状态")
        elif current_rsi < 30:
            st.success(f"✅ 当前RSI值: {current_rsi:.1f} - 股票可能处于超卖状态")
        else:
            st.info(f"ℹ️ 当前RSI值: {current_rsi:.1f} - 股票处于正常交易区间")
    
    # 数据表格
    st.markdown("---")
    st.markdown("### 📋 最近交易数据")
    
    # 格式化显示数据
    display_df = df.copy()
    display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
    display_df['涨跌幅'] = ((display_df['close'] / display_df['close'].shift(1) - 1) * 100).round(2)
    
    # 重命名列
    display_df = display_df[['date', 'open', 'high', 'low', 'close', 'volume', '涨跌幅']].rename(columns={
        'date': '日期',
        'open': '开盘价',
        'high': '最高价', 
        'low': '最低价',
        'close': '收盘价',
        'volume': '成交量'
    })
    
    # 数值格式化
    for col in ['开盘价', '最高价', '最低价', '收盘价']:
        display_df[col] = display_df[col].round(2)
    
    display_df['成交量'] = (display_df['成交量'] / 10000).astype(int).astype(str) + '万'
    display_df['涨跌幅'] = display_df['涨跌幅'].fillna(0).round(2).astype(str) + '%'
    
    st.dataframe(
        display_df.tail(10).reset_index(drop=True),
        use_container_width=True,
        height=350
    )
    
    # 底部信息
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #888888; padding: 20px; background-color: #2d2d2d; border-radius: 10px;">
        💡 <strong>Bloomberg Terminal Demo</strong> | 
        数据更新时间: {} | 
        🚀 基于Streamlit + Plotly构建 | 
        ⚠️ 模拟数据仅供演示使用
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
