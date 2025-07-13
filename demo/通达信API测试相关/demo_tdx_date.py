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
def get_minute_data_v2(stock_code='601318', count=800, frequency=8, market=None, host_info=None):
    """
    获取股票分钟线数据（改进版）
    
    Args:
        stock_code: 股票代码，默认为601318
        count: 获取数据条数，默认800条，最大800
        frequency: K线种类，默认8(1分钟)
                  0=5分钟, 1=15分钟, 2=30分钟, 3=1小时, 4=日K线
                  5=周K线, 6=月K线, 7=1分钟, 8=1分钟K线, 9=日K线
                  10=季K线, 11=年K线
        market: 市场代码，None时自动判断，0=深圳，1=上海
    
    Returns:
        DataFrame: 包含分钟线数据的DataFrame
    """
    # 自动判断市场
    if market is None:
        market = TDXParams.MARKET_SH if stock_code.startswith('6') else TDXParams.MARKET_SZ
    
    host_name, host_ip, host_port = host_info
    api = TdxHq_API()
    
    try:
        if api.connect(host_ip, host_port):
            print(f"已连接到服务器: {host_name}")
            
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

def get_minute_data(stock_code='601318', count=800, frequency=8, market=None):
    """
    获取股票分钟线数据
    
    Args:
        stock_code: 股票代码，默认为601318
        count: 获取数据条数，默认800条，最大800
        frequency: K线种类，默认8(1分钟)
                  0=5分钟, 1=15分钟, 2=30分钟, 3=1小时, 4=日K线
                  5=周K线, 6=月K线, 7=1分钟, 8=1分钟K线, 9=日K线
                  10=季K线, 11=年K线
        market: 市场代码，None时自动判断，0=深圳，1=上海
    
    Returns:
        DataFrame: 包含分钟线数据的DataFrame
    """
    # 自动判断市场
    if market is None:
        if stock_code.startswith('6'):
            market = TDXParams.MARKET_SH  # 上海市场
        else:
            market = TDXParams.MARKET_SZ  # 深圳市场
    
    # 随机选择一个行情服务器
    host = random.choice(hq_hosts)
    host_name, host_ip, host_port = host
    
    # 创建API对象
    api = TdxHq_API()
    
    try:
        # 连接服务器
        if api.connect(host_ip, host_port):
            print(f"已连接到服务器: {host_name} ({host_ip}:{host_port})")
            
            # 获取K线数据
            data = api.get_security_bars(frequency, market, stock_code, 0, count)
            
            if data:
                # 转换为DataFrame
                df = api.to_df(data)
                
                # 打印调试信息
                print(f"DataFrame列名: {df.columns.tolist()}")
                print(f"DataFrame数据类型: {df.dtypes}")
                
                # 转换时间格式为标准格式
                if 'datetime' in df.columns:
                    df['datetime'] = pd.to_datetime(df['datetime']).dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # 检查可用列并重新排列
                available_cols = df.columns.tolist()
                target_cols = ['datetime', 'open', 'high', 'low', 'close', 'vol', 'amount']
                final_cols = [col for col in target_cols if col in available_cols]
                
                if final_cols:
                    df = df[final_cols]
                    
                    # 如果vol存在，重命名为volume
                    if 'vol' in df.columns:
                        df = df.rename(columns={'vol': 'volume'})
                
                # 按时间排序
                if 'datetime' in df.columns:
                    df = df.sort_values('datetime').reset_index(drop=True)
                
                api.disconnect()
                return df
            else:
                print("未获取到数据")
                api.disconnect()
                return None
        else:
            print("连接服务器失败")
            return None
                
    except Exception as e:
        print(f"连接失败: {e}")
        return None

def get_realtime_quotes(stock_list):
    """
    获取多只股票的实时行情
    
    Args:
        stock_list: 股票代码列表，如['000001', '600300']
    
    Returns:
        DataFrame: 包含实时行情数据的DataFrame
    """
    # 构造查询列表，自动判断市场
    quotes_list = []
    for stock_code in stock_list:
        market = TDXParams.MARKET_SH if stock_code.startswith('6') else TDXParams.MARKET_SZ
        quotes_list.append((market, stock_code))
    
    host = random.choice(hq_hosts)
    host_name, host_ip, host_port = host
    api = TdxHq_API()
    
    try:
        if api.connect(host_ip, host_port):
            print(f"已连接到服务器: {host_name} ({host_ip}:{host_port})")
            
            # 获取实时行情
            data = api.get_security_quotes(quotes_list)
            
            if data:
                df = api.to_df(data)
                
                # 打印调试信息
                print(f"实时行情列名: {df.columns.tolist()}")
                
                api.disconnect()
                return df
            else:
                print("未获取到实时行情数据")
                api.disconnect()
                return None
        else:
            print("连接服务器失败")
            return None
                
    except Exception as e:
        print(f"获取实时行情失败: {e}")
        return None

def get_transaction_data(stock_code='601318', count=30):
    """
    获取分笔成交数据
    
    Args:
        stock_code: 股票代码
        count: 获取数据条数
    
    Returns:
        DataFrame: 包含分笔成交数据的DataFrame
    """
    # 自动判断市场
    market = TDXParams.MARKET_SH if stock_code.startswith('6') else TDXParams.MARKET_SZ
    
    host = random.choice(hq_hosts)
    host_name, host_ip, host_port = host
    api = TdxHq_API()
    
    try:
        if api.connect(host_ip, host_port):
            print(f"已连接到服务器: {host_name} ({host_ip}:{host_port})")
            
            # 获取分笔成交数据
            data = api.get_transaction_data(market, stock_code, 0, count)
            
            if data:
                df = api.to_df(data)
                
                # 打印调试信息
                print(f"分笔成交列名: {df.columns.tolist()}")
                
                api.disconnect()
                return df
            else:
                print("未获取到分笔成交数据")
                api.disconnect()
                return None
        else:
            print("连接服务器失败")
            return None
                
    except Exception as e:
        print(f"获取分笔成交数据失败: {e}")
        return None

if __name__ == "__main__":
    print("=" * 50)
    print("pytdx 数据获取测试")
    print("=" * 50)
    
    # 测试1：获取中国平安(601318)的1分钟线数据（改进版）
    print("\n1. 获取1分钟K线数据（改进版）:")
    df_1min = get_minute_data_v2('601318', count=10, frequency=8)
    if df_1min is not None:
        print(f"成功获取 {len(df_1min)} 条1分钟数据")
        print(df_1min.head())
        if 'datetime' in df_1min.columns:
            print(f"时间范围: {df_1min['datetime'].min()} 到 {df_1min['datetime'].max()}")
    
    # 测试2：获取5分钟K线数据（改进版）
    print("\n2. 获取5分钟K线数据（改进版）:")
    df_5min = get_minute_data_v2('601318', count=10, frequency=0)
    if df_5min is not None:
        print(f"成功获取 {len(df_5min)} 条5分钟数据")
        print(df_5min.head())
    
    # 测试3：获取实时行情
    print("\n3. 获取实时行情:")
    stock_list = ['000001', '600300', '601318']
    df_quotes = get_realtime_quotes(stock_list)
    if df_quotes is not None:
        print("实时行情数据:")
        print(df_quotes[['code', 'name', 'price', 'last_close', 'open', 'high', 'low']])
    
    # 测试4：获取分笔成交数据
    print("\n4. 获取分笔成交数据:")
    df_transaction = get_transaction_data('601318', count=5)
    if df_transaction is not None:
        print("分笔成交数据:")
        print(df_transaction)