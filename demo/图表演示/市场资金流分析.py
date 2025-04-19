"""
本模块用于分析整体市场资金流向:
1. 基于每只股票的OHLC和成交金额计算资金流入/流出
2. 聚合计算整体市场资金流向
3. 分析大盘资金流向与指数涨跌的关系
4. 可视化展示资金流向与指数变化
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
import akshare as ak
from datetime import datetime, timedelta
from tqdm import tqdm
import os

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

class MarketCapitalFlowAnalyzer:
    def __init__(self, benchmark_code='000001.SH'):
        """初始化市场资金流向分析器"""
        self.benchmark_code = benchmark_code
        self.benchmark_data = None
        self.stock_data = {}  # 存储各股票数据
        self.daily_capital_flow = {}  # 每日资金流向
        self.daily_sector_flow = {}  # 每日行业板块资金流向
        
    def load_benchmark_data(self, start_date, end_date):
        """加载基准指数数据"""
        print(f"加载 {self.benchmark_code} 指数数据...")
        # 使用akshare获取指数日线数据
        benchmark_data = ak.stock_zh_index_daily(symbol=self.benchmark_code)
        # 过滤日期范围
        benchmark_data = benchmark_data[(benchmark_data['date'] >= start_date) & 
                                       (benchmark_data['date'] <= end_date)]
        benchmark_data['date'] = pd.to_datetime(benchmark_data['date'])
        benchmark_data.set_index('date', inplace=True)
        self.benchmark_data = benchmark_data
        return benchmark_data
        
    def load_stock_data(self, stock_list, start_date, end_date):
        """加载多只股票的OHLC和成交金额数据"""
        print("加载个股交易数据...")
        for stock_code in tqdm(stock_list):
            try:
                # 使用akshare获取个股日线数据
                stock_data = ak.stock_zh_a_hist(symbol=stock_code, 
                                              start_date=start_date, 
                                              end_date=end_date,
                                              adjust="qfq")
                stock_data['日期'] = pd.to_datetime(stock_data['日期'])
                stock_data.set_index('日期', inplace=True)
                self.stock_data[stock_code] = stock_data
            except Exception as e:
                print(f"获取股票 {stock_code} 数据时出错: {e}")
        return self.stock_data
    
    def calculate_single_stock_flow(self, stock_data):
        """计算单只股票的资金流向"""
        # 复制数据以避免修改原始数据
        df = stock_data.copy()
        
        # 计算波动比率：(收盘价-开盘价)/(最高价-最低价)
        df['波动比率'] = df.apply(
            lambda row: (row['收盘'] - row['开盘']) / (row['最高'] - row['最低']) 
            if row['最高'] != row['最低'] else 0, axis=1
        )
        
        # 计算资金流向：波动比率 * 成交金额
        df['净资金流向'] = df['波动比率'] * df['成交额']
        
        # 为了保持与之前代码的一致性，还可以计算积极流入和消极流出
        df['积极流入'] = df['净资金流向'].apply(lambda x: x if x > 0 else 0)
        df['消极流出'] = df['净资金流向'].apply(lambda x: -x if x < 0 else 0)
        
        return df
    
    def calculate_market_capital_flow(self):
        """计算整体市场资金流向"""
        print("计算市场资金流向...")
        all_dates = sorted(set().union(*[set(self.stock_data[code].index) for code in self.stock_data]))
        
        # 初始化结果字典
        self.daily_capital_flow = {date: 0 for date in all_dates}
        
        # 计算每只股票的资金流向并累加
        for stock_code, stock_data in tqdm(self.stock_data.items()):
            flow_data = self.calculate_single_stock_flow(stock_data)
            
            for date, row in flow_data.iterrows():
                if pd.notna(row.get('净资金流向', np.nan)):
                    self.daily_capital_flow[date] += row['净资金流向'] / 100000000  # 转换为亿元
        
        # 转换为DataFrame
        self.flow_df = pd.DataFrame({
            '市场净资金流向(亿元)': self.daily_capital_flow
        })
        
        # 添加累计资金流向
        self.flow_df['累计净资金流向(亿元)'] = self.flow_df['市场净资金流向(亿元)'].cumsum()
        
        print("计算完成！")
        return self.flow_df
    
    def calculate_sector_capital_flow(self, sector_mapping):
        """计算板块资金流向"""
        print("计算板块资金流向...")
        # 初始化板块资金流向字典
        sectors = set(sector_mapping.values())
        dates = sorted(set().union(*[set(self.stock_data[code].index) for code in self.stock_data]))
        
        self.daily_sector_flow = {sector: {date: 0 for date in dates} for sector in sectors}
        
        # 计算每个板块的资金流向
        for stock_code, stock_data in tqdm(self.stock_data.items()):
            if stock_code not in sector_mapping:
                continue
                
            sector = sector_mapping[stock_code]
            flow_data = self.calculate_single_stock_flow(stock_data)
            
            for date, row in flow_data.iterrows():
                if pd.notna(row.get('净资金流向', np.nan)):
                    self.daily_sector_flow[sector][date] += row['净资金流向'] / 100000000  # 转换为亿元
        
        # 转换为DataFrame
        sector_flow_df = pd.DataFrame()
        for sector in sectors:
            sector_flow_df[f'{sector}净资金流向(亿元)'] = pd.Series(self.daily_sector_flow[sector])
        
        return sector_flow_df
    
    def visualize_capital_flow(self):
        """可视化市场资金流向与基准指数的关系"""
        if self.benchmark_data is None or not hasattr(self, 'flow_df'):
            print("请先加载基准指数数据并计算资金流向")
            return
            
        # 创建合并的数据框
        merged_data = pd.DataFrame(index=self.flow_df.index)
        merged_data['指数收盘价'] = self.benchmark_data['close']
        merged_data['市场净资金流向'] = self.flow_df['市场净资金流向(亿元)']
        merged_data['累计净资金流向'] = self.flow_df['累计净资金流向(亿元)']
        
        # 创建图表
        fig = plt.figure(figsize=(14, 10))
        gs = GridSpec(2, 1, height_ratios=[2, 1])
        
        # 基准指数图
        ax1 = fig.add_subplot(gs[0])
        ax1.plot(merged_data.index, merged_data['指数收盘价'], 'b-', label='指数收盘价')
        ax1.set_title(f'{self.benchmark_code}指数与市场资金流向分析', fontsize=15)
        ax1.set_ylabel('指数点位', fontsize=12)
        ax1.grid(True)
        ax1.legend(loc='upper left')
        
        # 创建资金流向的双y轴图
        ax2 = fig.add_subplot(gs[1], sharex=ax1)
        
        # 绘制日资金流向柱状图
        bars = ax2.bar(merged_data.index, merged_data['市场净资金流向'], 
                     color=merged_data['市场净资金流向'].apply(lambda x: 'red' if x > 0 else 'green'),
                     alpha=0.7, label='日资金流向(亿元)')
        
        # 设置柱状图y轴
        ax2.set_ylabel('日资金流向(亿元)', fontsize=12)
        ax2.tick_params(axis='y', labelcolor='b')
        ax2.grid(True, alpha=0.3)
        
        # 创建第二个y轴绘制累计资金流向
        ax3 = ax2.twinx()
        ax3.plot(merged_data.index, merged_data['累计净资金流向'], 'k-', label='累计资金流向(亿元)')
        ax3.set_ylabel('累计资金流向(亿元)', fontsize=12, color='k')
        ax3.tick_params(axis='y', labelcolor='k')
        
        # 合并图例
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax3.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # 设置x轴格式
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
        plt.gcf().autofmt_xdate()
        
        plt.tight_layout()
        plt.savefig('市场资金流向分析.png', dpi=300, bbox_inches='tight')
        plt.show()

def get_stock_list():
    """获取股票列表，可以根据需要修改为特定的股票池"""
    # 这里示例使用上证50成分股，实际应用中可以自定义
    try:
        df_stock_list = ak.index_stock_cons_weight_csindex(symbol="000016")  # 上证50成分股
        stock_list = df_stock_list['成份证券代码'].tolist()
        # 转换股票代码格式以适应akshare接口需求
        stock_list = [code.replace('.SH', '') for code in stock_list]
        stock_list = [code.replace('.SZ', '') for code in stock_list]
        return stock_list
    except Exception as e:
        print(f"获取股票列表时出错: {e}")
        # 如果出错，返回一个小的测试列表
        return ["600519", "000858", "601318", "600036", "000333"]

def main():
    # 创建分析器实例
    analyzer = MarketCapitalFlowAnalyzer(benchmark_code='000001.SH')
    
    # 设置日期范围
    start_date = '20230101'
    end_date = '20231231'
    
    # 加载基准指数数据
    benchmark_data = analyzer.load_benchmark_data(start_date, end_date)
    
    # 获取股票列表并加载数据
    stock_list = get_stock_list()
    stock_data = analyzer.load_stock_data(stock_list, start_date, end_date)
    
    # 计算市场资金流向
    flow_df = analyzer.calculate_market_capital_flow()
    print(flow_df.head())
    
    # 可视化结果
    analyzer.visualize_capital_flow()
    
    # 如果需要板块资金流向分析，可以添加如下代码
    # sector_mapping = {"600519": "消费", "000858": "消费", "601318": "金融", ...}
    # sector_flow = analyzer.calculate_sector_capital_flow(sector_mapping)
    # print(sector_flow.head())

if __name__ == "__main__":
    main()
