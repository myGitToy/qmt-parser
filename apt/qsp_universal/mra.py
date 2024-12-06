# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import tushare as ts
import akshare as ak
import sqlalchemy
import matplotlib.pyplot as plt
from datetime import datetime,timedelta
from apt.qsp_universal.base import base
from sqlalchemy.types import NVARCHAR , Float, Integer , Date

class MRA(base):
    """
    多元回归分析（Multiple Regression Analysis）
    计算股票与大盘的各项技术指标对比
    #该类用于计算股票与大盘的各项技术指标对比。        
    Attributes:
        BI_total_return (float): 总收益率
        BI_volatility (float): 年化波动率
        BI_correlation (float): 与市场相关系数
        BI_beta (float): Beta系数
        AI_sharpe_ratio (float): 夏普比率
        AI_max_drawdown (float): 最大回撤
        AI_info_ratio (float): 信息比率
        AI_up_capture (float): 上行捕获率
        AI_down_capture (float): 下行捕获率

    Methods:
        compare_with_market(benchmark='000001.sh'):
            比较个股与大盘的表现。
            Args:
                benchmark (str): 基准指数代码(默认上证指数)。
            Returns:
                DataFrame: 合并后的数据集。
                dict: 基础指标结果。
        calculate_metrics(benchmark='000001.sh', rf_rate=0.03):
            计算股票与大盘的各项技术指标对比。
            Args:
                benchmark (str): 基准指数代码(默认上证指数)。
                rf_rate (float): 无风险利率(年化)。
            Returns:
                DataFrame: 合并后的数据集。
                dict: 综合指标结果。
        plot_comparison_metrics(df, results):
            绘制对比图表。
            Args:
                df (DataFrame): 合并后的数据集。
                results (dict): 综合指标结果。
    """
    # 基础指标属性 Basic indicator attributes
    BI_total_return = 0.0  # 总收益率
    BI_volatility = 0.0    # 年化波动率
    BI_correlation = 0.0   # 与市场相关系数
    BI_beta = 0.0         # Beta系数

    # 进阶指标 Advanced indicator attributes
    AI_sharpe_ratio = 0.0  # 夏普比率
    AI_max_drawdown = 0.0  # 最大回撤
    AI_info_ratio = 0.0    # 信息比率
    AI_up_capture = 0.0    # 上行捕获率
    AI_down_capture = 0.0  # 下行捕获率



    def compare_with_market(self, benchmark='000001.sh'):
        """
        比较个股与大盘的表现（这里主要进行数据处理和基础值的计算）
        code: 股票代码
        benchmark: 基准指数代码(默认上证指数)
            其他几个常用的指标有：
                上证指数
                深圳成指
                中小板指数
                创业板指数
        """        
        # 获取证券代码的数据并按规则进行数据清洗
        stock_data = self.get_k_data()
        stock_data['date'] = pd.to_datetime(stock_data['date'])
        stock_data.sort_values('date', inplace=True)
        # 获取指数的数据并按规则进行数据清洗（使用tspro API接口）
        market_data = self.pro.index_daily(ts_code = benchmark , start_date = self.start_date.strftime('%Y%m%d') , end_date = self.end_date.strftime('%Y%m%d'))
        market_data.rename(columns={'ts_code':'code','trade_date':'date'},inplace=True)
        market_data['date'] = pd.to_datetime(market_data['date'])
        market_data.sort_values('date', inplace=True)  
        # 打印并测试数据
        print(stock_data)
        print(market_data)
        # 确保两个数据集的日期对齐
        df = pd.merge(stock_data, market_data, on='date', suffixes=('_stock', '_market'))
        # 升序排列
        df.sort_values('date', inplace=True)
        # ------> TODO: 这里可能还需要对停牌的数据做缺失值处理
        # 计算日收益率
        df['return_stock'] = df['close_stock'].pct_change()
        df['return_market'] = df['close_market'].pct_change()
        # TODO 后续所有的计算都是基于收益率指标的，非量价指标
        # 后续如果需要使用量价指标，需要添加计算
        """
        是的,大多数风险收益指标都是基于收益率(returns)计算的,而不是直接使用价格。原因如下:

        ### 1. 为什么使用收益率
        - **可比性**: 不同价格区间的股票可以直接比较
        - **平稳性**: 收益率序列通常更符合统计分析要求
        - **标准化**: 便于跨市场、跨时期比较
        - **对数正态分布**: 收益率通常更接近正态分布

        ### 2. 常用收益率计算方式
        ```python
        # 简单收益率
        simple_returns = (price_t - price_t_1) / price_t_1

        # 对数收益率
        log_returns = np.log(price_t / price_t_1)
        ```
        ### 3. 其他数据的用途
        虽然核心指标基于收益率,但其他数据也有重要作用:
        - **开盘/收盘价**:
        - 计算日内波动指标
        - 技术分析形态
        - 缺口分析
        - **成交量**:
        - 流动性分析
        - 市场情绪指标
        - 价量配合分析
        - 能量潮指标(OBV)
        """
        def calculate_volume_indicators(df):
            """计算成交量相关指标，基于整合好的数据集，目的见上面的注释"""
            # 成交量加权价格
            df['vwap'] = (df['volume'] * df['close']).cumsum() / df['volume'].cumsum()            
            # 价量趋势
            df['price_volume_trend'] = df['close'].pct_change() * df['volume']
            # 日内波动
            df['intraday_volatility'] = (df['high'] - df['low']) / df['open']            
            return df   
             
        # 计算累积收益率
        df['cum_return_stock'] = (1 + df['return_stock']).cumprod() - 1
        df['cum_return_market'] = (1 + df['return_market']).cumprod() - 1
        
        # 计算波动率(年化)
        vol_stock = df['return_stock'].std() * np.sqrt(252)
        vol_market = df['return_market'].std() * np.sqrt(252)
        
        # 计算相关系数
        """
        范围: -1 到 1
        含义: 衡量两个变量之间的线性关系强度
        解读:
        1: 完全正相关
        -1: 完全负相关
        0: 无线性相关
        """
        correlation = df['return_stock'].corr(df['return_market'])
        
        # 计算Beta系数
        """
        含义: 衡量个股对市场波动的敏感度
        解读:
        β > 1: 股票波动大于市场
        β < 1: 股票波动小于市场
        β = 1: 与市场同步波动
        PS 这是一个相对指标，衡量两个收益率序列的关系 时间尺度的变化不会影响这个比值
        """
        beta = df['return_stock'].cov(df['return_market']) / df['return_market'].var()
        
        # 汇总结果
        results = {
            '股票代码': self.code,
            '总收益率_个股': f'{df["cum_return_stock"].iloc[-1]:.2%}',
            '总收益率_大盘': f'{df["cum_return_market"].iloc[-1]:.2%}',
            '年化波动率_个股': f'{vol_stock:.2%}',
            '年化波动率_大盘': f'{vol_market:.2%}',
            '相关系数': f'{correlation:.2f}',
            'Beta系数': f'{beta:.2f}'
        }
        print(results)
        return df, results

    def calculate_metrics(self,  benchmark='000001.sh', rf_rate=0.03 , anaual_trade_day = 252):
        """
        计算股票与大盘的各项技术指标对比
        params:
            rf_rate: 无风险利率(年化)
        返回DateFrame和结果字典
        """
        #TODO: 无风险利率可以采用这种方法pro = ts.pro_api()
        #df = pro.shibor(start_date='20180101', end_date='20181101')
        # 获取数据并合并
        df, basic_results = self.compare_with_market(benchmark)
        
        # 计算日化无风险利率
        # TODO 注意可能后续会更改无风险收益的数据公式和获取来源
        daily_rf = (1 + rf_rate) ** (1/anaual_trade_day) - 1
        
        def calculate_correlation(return_stock, return_market):
            """
            未实装 result有替代的计算方法
            # 计算相关系数
            相关系数 (Correlation)
            范围: -1 到 1
            含义: 衡量两个变量之间的线性关系强度
            解读:
            1: 完全正相关
            -1: 完全负相关
            0: 无线性相关
            """
            return return_stock.corr(return_market)    
        def calculate_r_squared(stock_returns, market_returns):
            """计算R平方"""
            correlation = stock_returns.corr(market_returns)
            return correlation ** 2
        
        def calculate_treynor(stock_returns, market_returns, rf_rate):
            """计算特雷诺比率"""
            beta = calculate_beta(stock_returns, market_returns)
            excess_return = stock_returns.mean() * anaual_trade_day - rf_rate
            return excess_return / beta
        
        def calculate_jensen_alpha(stock_returns, market_returns, rf_rate):
            """计算詹森指数"""
            beta = calculate_beta(stock_returns, market_returns)
            expected_return = rf_rate + beta * (market_returns.mean() * anaual_trade_day - rf_rate)
            actual_return = stock_returns.mean() * anaual_trade_day
            return actual_return - expected_return
        
        def calculate_drawdown(returns):
            """计算最大回撤"""
            cum_returns = (1 + returns).cumprod()
            rolling_max = cum_returns.expanding().max()
            drawdowns = cum_returns / rolling_max - 1
            return drawdowns.min()
        
        def calculate_sharpe(returns):
            """计算夏普比率"""
            excess_returns = returns - daily_rf
            return np.sqrt(anaual_trade_day) * excess_returns.mean() / returns.std()
        
        def calculate_capture_ratios(stock_returns, market_returns):
            """计算上下行捕获率"""
            up_market = market_returns > 0
            down_market = market_returns < 0
            
            up_capture = (stock_returns[up_market].mean() / market_returns[up_market].mean()) if len(market_returns[up_market]) > 0 else 0
            down_capture = (stock_returns[down_market].mean() / market_returns[down_market].mean()) if len(market_returns[down_market]) > 0 else 0
            
            return up_capture, down_capture
        
        def calculate_alpha(stock_returns, market_returns, rf_rate):
            """
            计算Alpha系数    
            Args:
                stock_returns: 股票收益率序列
                market_returns: 市场收益率序列
                rf_rate: 无风险利率
                mode: 'annual'(年化) / 'total'(区间总计)  
            Returns:          
                Alpha > 0：表示投资组合的表现优于市场预期
                Alpha < 0：表示投资组合的表现低于市场预期
                Alpha = 0：表示投资组合的表现符合市场预期
            """ 
            beta = calculate_beta(stock_returns, market_returns) #beta系数无需年化处理
            stock_mean = stock_returns.mean() * anaual_trade_day
            market_mean = market_returns.mean() * anaual_trade_day
            # 根据 CAPM 模型预期的超额收益 = beta * (market_mean - rf_rate):
            return stock_mean - (rf_rate + beta * (market_mean - rf_rate))       
        
        def calculate_beta(stock_returns, market_returns):
            """计算Beta系数
            Beta系数衡量个股相对于市场的敏感度
            β > 1: 股票波动大于市场
            β < 1: 股票波动小于市场
            β = 1: 与市场同步波动
            """
            return stock_returns.cov(market_returns) / market_returns.var()
        
        # 计算各项指标
        stock_returns = df['return_stock']
        market_returns = df['return_market']
        
        # 最大回撤
        max_dd_stock = calculate_drawdown(stock_returns)
        max_dd_market = calculate_drawdown(market_returns)
        
        # 夏普比率
        sharpe_stock = calculate_sharpe(stock_returns)
        sharpe_market = calculate_sharpe(market_returns)
        
        # 信息比率
        excess_returns = stock_returns - market_returns
        info_ratio = np.sqrt(252) * excess_returns.mean() / excess_returns.std()
        
        # 上下行捕获率
        up_capture, down_capture = calculate_capture_ratios(stock_returns, market_returns)
        
        # 合并结果
        advanced_results = {
            '最大回撤_个股': max_dd_stock,
            '最大回撤_大盘': max_dd_market,
            '夏普比率_个股': sharpe_stock,
            '夏普比率_大盘': sharpe_market,
            '信息比率': info_ratio,
            '上行捕获率': up_capture,
            '下行捕获率': down_capture
        }
        
        results = {**basic_results, **advanced_results}
        
        # 可视化
        self.plot_comparison_metrics(df, results)
        
        return df, results

    def plot_comparison_metrics(self, df, results):
        """绘制对比图表"""        
        plt.style.use('seaborn')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 累积收益对比
        axes[0,0].plot(df['date'], df['cum_return_stock'], label='个股')
        axes[0,0].plot(df['date'], df['cum_return_market'], label='大盘')
        axes[0,0].set_title('累积收益对比')
        axes[0,0].legend()
        axes[0,0].grid(True)
        
        # 滚动波动率
        rolling_vol_stock = df['return_stock'].rolling(window=21).std() * np.sqrt(252)
        rolling_vol_market = df['return_market'].rolling(window=21).std() * np.sqrt(252)
        axes[0,1].plot(df['date'], rolling_vol_stock, label='个股')
        axes[0,1].plot(df['date'], rolling_vol_market, label='大盘')
        axes[0,1].set_title('滚动波动率(年化)')
        axes[0,1].legend()
        
        # 滚动相关性
        rolling_corr = df['return_stock'].rolling(window=63).corr(df['return_market'])
        axes[1,0].plot(df['date'], rolling_corr)
        axes[1,0].set_title('滚动相关系数(63天)')
        
        # 回撤对比
        cum_returns_stock = (1 + df['return_stock']).cumprod()
        cum_returns_market = (1 + df['return_market']).cumprod()
        dd_stock = cum_returns_stock / cum_returns_stock.expanding().max() - 1
        dd_market = cum_returns_market / cum_returns_market.expanding().max() - 1
        axes[1,1].plot(df['date'], dd_stock, label='个股')
        axes[1,1].plot(df['date'], dd_market, label='大盘')
        axes[1,1].set_title('回撤分析')
        axes[1,1].legend()
        
        plt.tight_layout()
        plt.show()

# 使用示例
if __name__ == "__main__":
    mra = MRA()
    mra.vendor = base.vendor.akshare
    mra.fq = base.复权.动态复权
    mra.start_date = datetime(2024, 1, 1)
    mra.end_date = datetime(2024, 11, 25)
    mra.ktype = '1d'
    mra.code = '510300.sh'
    #mra.compare_with_market()
    # 计算股票与大盘的各项技术指标对比
    mra.calculate_metrics()
    df, results = mra.calculate_metrics()
    print("\n分析结果:")
    for k, v in results.items():
        print(f"{k}: {v:.4f}")