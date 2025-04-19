import pandas as pd

def calculate_money_flow(df):
    """
    计算资金流入流出指标
    :param df: 包含OHLC和成交量数据的DataFrame
    :return: 添加资金流量指标的DataFrame
    """
    # 计算典型价格
    df['Typical Price'] = (df['High'] + df['Low'] + df['Close']) / 3
    
    # 计算资金流量
    df['Money Flow'] = df['Typical Price'] * df['Volume']
    
    # 标记正向和负向资金流量
    df['Positive Flow'] = df['Money Flow'].where(df['Close'] > df['Close'].shift(1), 0)
    df['Negative Flow'] = df['Money Flow'].where(df['Close'] <= df['Close'].shift(1), 0)
    
    # 计算资金流量比率
    df['Money Flow Ratio'] = df['Positive Flow'].rolling(window=14).sum() / \
                             df['Negative Flow'].rolling(window=14).sum()
    
    # 计算资金流量指数（MFI）
    df['MFI'] = 100 - (100 / (1 + df['Money Flow Ratio']))
    
    return df

# 示例数据
data = {
    'High': [120, 125, 130, 128, 132],
    'Low': [115, 120, 125, 123, 128],
    'Close': [118, 123, 128, 126, 130],
    'Volume': [1000, 1100, 1050, 1020, 1080]
}
df = pd.DataFrame(data)

# 计算资金流量指标
df = calculate_money_flow(df)
print(df[['Typical Price', 'Money Flow', 'MFI']])
