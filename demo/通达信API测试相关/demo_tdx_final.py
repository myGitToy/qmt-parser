from pytdx.hq import TdxHq_API
from pytdx.params import TDXParams
from pytdx.config.hosts import hq_hosts
import pandas as pd
from datetime import datetime
import random

def try_multiple_servers(func):
    """
    装饰器：尝试多个服务器直到成功
    """
    def wrapper(*args, **kwargs):
        # 随机打乱服务器列表
        servers = hq_hosts.copy()
        random.shuffle(servers)
        
        for host in servers[:5]:  # 只尝试前5个服务器
            try:
                host_name, host_ip, host_port = host
                print(f"尝试连接服务器: {host_name} ({host_ip}:{host_port})")
                
                # 将服务器信息传递给原函数
                result = func(*args, **kwargs, host_info=(host_name, host_ip, host_port))
                if result is not None:
                    return result
                    
            except Exception as e:
                print(f"服务器 {host_name} 连接失败: {e}")
                continue
        
        print("所有服务器都连接失败")
        return None
    
    return wrapper

@try_multiple_servers
def get_k_data(stock_code='601318', count=800, frequency=8, market=None, host_info=None):
    """
    获取股票K线数据
    
    Args:
        stock_code: 股票代码
        count: 获取数据条数，最大800
        frequency: K线种类
                  0=5分钟, 1=15分钟, 2=30分钟, 3=1小时, 4=日K线
                  5=周K线, 6=月K线, 7=1分钟, 8=1分钟K线, 9=日K线
                  10=季K线, 11=年K线
        market: 市场代码，None时自动判断
        host_info: 服务器信息（由装饰器传入）
    
    Returns:
        DataFrame: 包含K线数据的DataFrame
    """
    # 自动判断市场
    if market is None:
        market = TDXParams.MARKET_SH if stock_code.startswith('6') else TDXParams.MARKET_SZ
    
    host_name, host_ip, host_port = host_info
    api = TdxHq_API()
    
    try:
        if api.connect(host_ip, host_port):
            print(f"✓ 已连接到服务器: {host_name}")
            
            # 获取K线数据
            data = api.get_security_bars(frequency, market, stock_code, 0, count)
            
            if data:
                df = api.to_df(data)
                
                # 转换时间格式
                if 'datetime' in df.columns:
                    df['datetime'] = pd.to_datetime(df['datetime']).dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # 标准化列名
                if 'vol' in df.columns:
                    df = df.rename(columns={'vol': 'volume'})
                
                # 选择需要的列
                available_cols = df.columns.tolist()
                target_cols = ['datetime', 'open', 'high', 'low', 'close', 'volume', 'amount']
                final_cols = [col for col in target_cols if col in available_cols]
                
                if final_cols:
                    df = df[final_cols]
                
                # 按时间排序
                if 'datetime' in df.columns:
                    df = df.sort_values('datetime').reset_index(drop=True)
                
                api.disconnect()
                return df
            
            api.disconnect()
            
    except Exception as e:
        print(f"数据获取失败: {e}")
        
    return None

@try_multiple_servers
def get_realtime_quotes(stock_list, host_info=None):
    """
    获取多只股票的实时行情
    
    Args:
        stock_list: 股票代码列表
        host_info: 服务器信息（由装饰器传入）
    
    Returns:
        DataFrame: 包含实时行情数据的DataFrame
    """
    # 构造查询列表
    quotes_list = []
    for stock_code in stock_list:
        market = TDXParams.MARKET_SH if stock_code.startswith('6') else TDXParams.MARKET_SZ
        quotes_list.append((market, stock_code))
    
    host_name, host_ip, host_port = host_info
    api = TdxHq_API()
    
    try:
        if api.connect(host_ip, host_port):
            print(f"✓ 已连接到服务器: {host_name}")
            
            # 获取实时行情
            data = api.get_security_quotes(quotes_list)
            
            if data:
                df = api.to_df(data)
                api.disconnect()
                return df
            
            api.disconnect()
            
    except Exception as e:
        print(f"实时行情获取失败: {e}")
        
    return None

@try_multiple_servers
def get_transaction_data(stock_code='601318', count=30, host_info=None):
    """
    获取分笔成交数据
    
    Args:
        stock_code: 股票代码
        count: 获取数据条数
        host_info: 服务器信息（由装饰器传入）
    
    Returns:
        DataFrame: 包含分笔成交数据的DataFrame
    """
    # 自动判断市场
    market = TDXParams.MARKET_SH if stock_code.startswith('6') else TDXParams.MARKET_SZ
    
    host_name, host_ip, host_port = host_info
    api = TdxHq_API()
    
    try:
        if api.connect(host_ip, host_port):
            print(f"✓ 已连接到服务器: {host_name}")
            
            # 获取分笔成交数据
            data = api.get_transaction_data(market, stock_code, 0, count)
            
            if data:
                df = api.to_df(data)
                api.disconnect()
                return df
            
            api.disconnect()
            
    except Exception as e:
        print(f"分笔成交数据获取失败: {e}")
        
    return None

def get_frequency_name(frequency):
    """获取频率名称"""
    freq_map = {
        0: '5分钟', 1: '15分钟', 2: '30分钟', 3: '1小时', 4: '日K线',
        5: '周K线', 6: '月K线', 7: '1分钟', 8: '1分钟K线', 9: '日K线',
        10: '季K线', 11: '年K线'
    }
    return freq_map.get(frequency, f'未知频率({frequency})')

if __name__ == "__main__":
    print("=" * 60)
    print("pytdx 完整数据获取测试")
    print("=" * 60)
    
    # 测试股票代码
    test_stocks = ['601318', '000001', '600519']
    
    # 测试1：获取不同频率的K线数据
    print("\n📊 测试1: 获取不同频率的K线数据")
    frequencies = [8, 0, 1, 4]  # 1分钟、5分钟、15分钟、日K线
    
    for freq in frequencies:
        print(f"\n🔹 获取{get_frequency_name(freq)}数据:")
        df = get_k_data('601318', count=5, frequency=freq)
        if df is not None:
            print(f"✓ 成功获取 {len(df)} 条数据")
            print(df.head(3))
            if 'datetime' in df.columns:
                print(f"📅 时间范围: {df['datetime'].min()} 到 {df['datetime'].max()}")
        else:
            print("❌ 数据获取失败")
        print("-" * 40)
    
    # 测试2：获取实时行情
    print("\n📈 测试2: 获取实时行情")
    df_quotes = get_realtime_quotes(test_stocks)
    if df_quotes is not None:
        print("✓ 实时行情数据:")
        print(df_quotes.head())
        print(f"📊 列名: {df_quotes.columns.tolist()}")
    else:
        print("❌ 实时行情获取失败")
    
    # 测试3：获取分笔成交数据
    print("\n📊 测试3: 获取分笔成交数据")
    df_transaction = get_transaction_data('601318', count=5)
    if df_transaction is not None:
        print("✓ 分笔成交数据:")
        print(df_transaction.head())
        print(f"📊 列名: {df_transaction.columns.tolist()}")
    else:
        print("❌ 分笔成交数据获取失败")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
