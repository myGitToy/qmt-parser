"""
本模块用于演示9090功能，具体说明如下：
1. 统计每天上涨的股票数量与总交易股票的比值
2. 统计每天下跌的股票总流通市值与总交易股票流通市值的比值
4. 上述统计内容与上证指数同步出图，附图叠加，折线图

如果比率超过90%，则用表示市场情绪严重乐观，比例小于10%，则表示市场情绪严重悲观

"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
import akshare as ak
from datetime import datetime, timedelta
from tqdm import tqdm
from apt.qsp_universal.base import base as base
from apt.vendor.tspro.base import base as tspro_base
from apt.vendor.tspro.pro_api import pro_api as pro_api

from apt.vendor.tspro.data import data as tspro_data

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

class MarketSentimentAnalyzer(pro_api):
    def __init__(self , benchmark_code = '000001.SH'):
        """初始化市场情绪分析器"""
        self.daily_up_ratio = {}  # 每天上涨股票数量比例
        self.daily_down_mv_ratio = {}  # 每天下跌股票市值比例
        super().__init__()
        # 设置基准指数代码
        self.benchmark_code = benchmark_code 
        # 设置基准指数数据
        self.df_index = pd.DataFrame()

    def merge_index_data(self) -> pd.DataFrame:
        """
        整合指数数据
        一般含有OHLC和流通市值等数据
        通过pro_api两个接口获取数据并聚合而成
        """
        print("开始计算指数数据...")
        df_index_data = self.get_index_daily(index_code=self.benchmark_code)
        df_index_basic = self.get_index_dailybasic(index_code=self.benchmark_code)
        # 两张表合并，并设置索引
        self.df_index = pd.merge(df_index_data, df_index_basic, on='date', how='inner')
        return self.df_index
    
    def calculate_daily_ratios(self):
        """计算每日上涨比例和下跌市值比例"""
        print("开始计算每日市场情绪指标...")
        # 获取交易日期
        if not self.df_index.empty :
            trading_dates = self.df_index['date'].tolist()    
        else:
            raise ValueError("指数数据为空，请先加载指数数据。") 
        
        for date in tqdm(trading_dates):
            try:
                # 获取当日A股所有股票行情
                stock_data = ak.stock_zh_a_spot_em()
                
                # 计算上涨股票数量比例
                total_stocks = len(stock_data)
                up_stocks = len(stock_data[stock_data['涨跌幅'] > 0])
                up_ratio = up_stocks / total_stocks * 100 if total_stocks > 0 else 0
                
                # 计算下跌股票市值比例
                total_mv = stock_data['流通市值'].sum()
                down_stocks_mv = stock_data[stock_data['涨跌幅'] < 0]['流通市值'].sum()
                down_mv_ratio = down_stocks_mv / total_mv * 100 if total_mv > 0 else 0
                
                # 存储结果
                date_obj = datetime.strptime(date, '%Y%m%d')
                self.daily_up_ratio[date_obj] = up_ratio
                self.daily_down_mv_ratio[date_obj] = down_mv_ratio
            
            except Exception as e:
                print(f"处理日期 {date} 时出错: {e}")
        
        # 转换为DataFrame
        self.ratio_df = pd.DataFrame({
            '上涨比例': self.daily_up_ratio,
            '下跌市值比例': self.daily_down_mv_ratio
        })
        print("计算完成！")
        return self.ratio_df
    
    def visualize_market_sentiment(self):
        """可视化市场情绪指标和上证指数"""
        # 创建合并的数据框
        merged_data = pd.DataFrame(index=self.index_data.index)
        merged_data['上证指数'] = self.index_data['close']
        merged_data['上涨比例'] = pd.Series(self.daily_up_ratio)
        merged_data['下跌市值比例'] = pd.Series(self.daily_down_mv_ratio)
        
        # 创建图表
        fig = plt.figure(figsize=(14, 10))
        gs = GridSpec(3, 1, height_ratios=[2, 1, 1])
        
        # 上证指数图
        ax1 = fig.add_subplot(gs[0])
        ax1.plot(merged_data.index, merged_data['上证指数'], 'b-', label='上证指数')
        ax1.set_title('9090市场情绪分析', fontsize=15)
        ax1.set_ylabel('指数点位', fontsize=12)
        ax1.grid(True)
        ax1.legend(loc='upper left')
        
        # 上涨比例图
        ax2 = fig.add_subplot(gs[1], sharex=ax1)
        ax2.plot(merged_data.index, merged_data['上涨比例'], 'r-', label='上涨股票比例(%)')
        ax2.axhline(y=90, color='r', linestyle='--', alpha=0.7, label='90%极度乐观线')
        ax2.axhline(y=10, color='g', linestyle='--', alpha=0.7, label='10%极度悲观线')
        ax2.fill_between(merged_data.index, 90, merged_data['上涨比例'], 
                        where=(merged_data['上涨比例'] >= 90), color='r', alpha=0.3)
        ax2.fill_between(merged_data.index, merged_data['上涨比例'], 10, 
                        where=(merged_data['上涨比例'] <= 10), color='g', alpha=0.3)
        ax2.set_ylabel('上涨比例(%)', fontsize=12)
        ax2.set_ylim(0, 100)
        ax2.grid(True)
        ax2.legend(loc='upper left')
        
        # 下跌市值比例图
        ax3 = fig.add_subplot(gs[2], sharex=ax1)
        ax3.plot(merged_data.index, merged_data['下跌市值比例'], 'g-', label='下跌股票市值比例(%)')
        ax3.axhline(y=90, color='g', linestyle='--', alpha=0.7, label='90%极度悲观线')
        ax3.axhline(y=10, color='r', linestyle='--', alpha=0.7, label='10%极度乐观线')
        ax3.fill_between(merged_data.index, 90, merged_data['下跌市值比例'], 
                        where=(merged_data['下跌市值比例'] >= 90), color='g', alpha=0.3)
        ax3.fill_between(merged_data.index, merged_data['下跌市值比例'], 10, 
                        where=(merged_data['下跌市值比例'] <= 10), color='r', alpha=0.3)
        ax3.set_ylabel('下跌市值比例(%)', fontsize=12)
        ax3.set_ylim(0, 100)
        ax3.grid(True)
        ax3.legend(loc='upper left')
        
        # 设置x轴格式
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
        plt.gcf().autofmt_xdate()
        
        plt.tight_layout()
        plt.savefig('9090市场情绪分析.png', dpi=300, bbox_inches='tight')
        plt.show()

def main():
    # 创建分析器实例
    analyzer = MarketSentimentAnalyzer(benchmark_code='000001.SH')
    analyzer.start_date = datetime(2025,1,1)
    analyzer.end_date = datetime.now()
    
    # 获取数据并计算
    df_index = analyzer.merge_index_data()
    # 
    print(df_index[['date', 'close','float_mv']])
    analyzer.calculate_daily_ratios()
    
    # 可视化结果
    analyzer.visualize_market_sentiment()

if __name__ == "__main__":
    main()