"""
测试截面数据的RankIC和RankICIR
统计学指标介绍
RankIC（斯皮尔曼秩相关系数）：
    1. 斯皮尔曼相关系数对样本量是敏感的，样本量越小，RankIC的波动性越大。
    2. RankIC的值域为[-1, 1]，值越接近1表示正相关性越强，值越接近-1表示负相关性越强，值接近0表示无相关性。
    3. RankIC 均值	0.02 (微弱)	0.03 - 0.06 (尚可)	0.06 - 0.10 (良好)
RankICIR（RankIC信息比率）：
    1. ICIR 衡量的是 RankIC 的稳定性，值越大表示 RankIC 越稳定。
    2. 0.02 (极差)	0.5 - 0.8 (可用)	> 1.0 (优秀)
    3. RankICIR = Mean(RankIC) / Std(RankIC)
"""

"""
其他待研究

因子名称	RankIC均值	RankIC标准差	RankICIR	IC胜率	最大回撤期
价值因子	0.05	0.04	1.25	58%	低
动量因子	0.06	0.06	1.00	55%	中
质量因子	0.03	0.03	1.00	52%	低
市场环境分析：

将回测期划分为牛市、熊市、震荡市。

分析每个因子在不同市场环境下的RankIC和RankICIR。例如，低波动因子可能在熊市表现更好，而动量因子在牛市表现更佳。这有助于构建适应不同市场状况的智能模型。

RankICIR是核心比较指标：在大多数情况下，RankICIR是比RankIC均值更重要的比较维度，因为它直接衡量了因子表现的稳定性和可靠性。一个高ICIR的因子是构建稳健策略的基石。

不要只看一个指标：要结合RankIC均值、RankICIR、胜率、衰减、相关性等进行综合判断。

可视化：绘制每个因子的IC序列图、累计IC图、IC衰减图，可以非常直观地进行比较。

定期重检：因子的有效性会随着市场变化而衰减或变化，需要定期重复这个比较过程，对因子库进行更新。
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from apt.vendor.akshare.data import data as ak_data
from datetime import datetime
from apt.vendor.akshare.security import security as ak_security
# typing.Literal may not be available on very old Python versions; fall back to typing_extensions if needed
try:
    from typing import Literal
except Exception:
    from typing_extensions import Literal


class RankIC(ak_data,ak_security):
    def __init__(self,params = {}):
        """
        接受的数据矩阵样例
        日期 代码 因子值

        简单的例子，每日资金流向对于成交金额的占比作为因子：
        2025/1/4 000001.SZ 0.3
        ...
        2025/12/31 899802.SH -0.1

        上述数据构成了2025全年资金流向占比的因子数据，然后统计N日的收益率，从而计算RankIC和RankICIR，以检验因子的有效性
        备注：以上数据可以拆分成全市场或者某一个板块，但是不同板块间的IC指标不可拿来一起比较，没有意义
        """
        super(ak_data, self).__init__()
        super(ak_security, self).__init__()
        #self.data = data  # 假设data是一个DataFrame，包含日期、代码、因子值等信息
        self.params = params


    def calculate_rank_ic(self):
        # 计算RankIC的逻辑
        pass

    def calculate_rank_icir(self):
        # 计算RankICIR的逻辑
        pass

    def get_data(self):
        pass
    
    def prepare_data(self):
        """
        数据准备阶段，数据表的格式
        code date factor_flow_pct profit is_suspended
        证券代码 日期 因子值 N日收益率 停牌标记
        
        【停牌数据处理说明】
        停牌会影响RankIC计算的准确性，主要问题：
        1. 样本偏差：停牌股票通常涉及重大事项，复牌后波动大
        2. 前视偏差：计算因子时股票正常，但未来N日内停牌无法交易
        3. 数据缺失：停牌期间无价格数据，导致收益率为NaN
        
        处理方案（通过 self.handle_suspension 参数控制）：
        - 'exclude' (默认推荐)：排除当日或未来N日内有停牌的样本
          优点：避免偏差，结果更可靠
          缺点：减少样本量，特别是在停牌频繁的时期
          
        - 'keep'：保留所有数据，停牌样本收益为NaN
          优点：保持完整样本
          缺点：RankIC计算会自动跳过NaN，可能引入偏差
          
        - 'forward_fill'：用最后有效价格填充（谨慎使用）
          优点：不损失样本
          缺点：假设停牌期间价格不变，不符合实际，可能严重扭曲结果
        
        【使用示例】
        data = RankIC()
        data.handle_suspension = 'exclude'  # 或 'keep', 'forward_fill'
        data.prepare_data()
        
        获取所有股票代码
            code  symbol   name market   list_date
            000001.SZ  000001   平安银行     主板  1991-04-03
            000002.SZ  000002    万科A     主板  1991-01-29
            000004.SZ  000004  *ST国华     主板  1991-01-14
            000006.SZ  000006   深振业A     主板  1992-04-27
            000007.SZ  000007    全新好     主板  1992-04-13
            [5437 rows x 5 columns]      

        获取交易日历
            date  is_open
            0   2025-01-02        1
            1   2025-01-03        1
            ..         ...      ...
            181 2025-09-29        1
            182 2025-09-30        1
            [183 rows x 2 columns]   

        【逻辑】
            1. 获取所有股票代码
            2. 按照一定的逻辑规则筛选选股池（比如市值，板块）
            3. 构造股票代码和交易日的笛卡尔积，作为基础表
        """
        df_all_code = self.get_all_code(type = ['stock'],day = self.end_date)[['code']]
        df_trade_date = self.get_calendar()
        print(df_trade_date)
        print(df_all_code)
        # 构造交易日和股票代码的笛卡尔积作为基础表
        codes = df_all_code['code'].astype(str).tolist()
        # 兼容日期列名字及筛选开盘日
        if 'is_open' in df_trade_date.columns:
            trade_dates = df_trade_date.loc[df_trade_date['is_open'] == 1, 'date']
        else:
            trade_dates = df_trade_date['date']
        trade_dates = pd.to_datetime(trade_dates)
        trade_dates = trade_dates[(trade_dates >= pd.to_datetime(self.start_date)) & (trade_dates <= pd.to_datetime(self.end_date))]
        trade_dates = sorted(list(pd.DatetimeIndex(trade_dates).unique()))

        if len(codes) == 0 or len(trade_dates) == 0:
            # 保证返回稳定结构
            self.prepared_data = pd.DataFrame(columns=['code', 'date', 'factor_flow_pct', 'profit'])
            return self.prepared_data

        idx = pd.MultiIndex.from_product([codes, trade_dates], names=['code', 'date'])
        df = pd.DataFrame(index=idx).reset_index()

        # 优先尝试使用已提供的因子数据 self.data（格式需含 code/date/factor_flow_pct）
        if hasattr(self, 'data') and self.data is not None:
            try:
                tmp = self.data.copy()
                if 'date' in tmp.columns:
                    tmp['date'] = pd.to_datetime(tmp['date'])
                df = df.merge(tmp[['code', 'date', 'factor_flow_pct']].drop_duplicates(), on=['code', 'date'], how='left')
            except Exception:
                df['factor_flow_pct'] = np.nan
        else:
            # 如果没有外部因子数据，初始化因子列（可在外部填充）
            df['factor_flow_pct'] = np.nan

        # 计算 N 日的未来收益率（forward return），默认 N=5，可通过 self.n 覆盖
        n = int(getattr(self, 'n', 5))

        # 尝试多个常见的方法名去获取某只股票的历史数据，返回按日期索引的 close 序列
        def _fetch_close_series(code):
            candidate_methods = [
                'get_price', 'get_hist_price', 'get_daily', 'get_price_history',
                'get_k_data', 'get_bars', 'get_security_price', 'get_history'
            ]
            for m in candidate_methods:
                if hasattr(self, m):
                    try:
                        func = getattr(self, m)
                        # 尝试不同常见签名（部分 wrapper 接口接受 (code, start, end, ktype)）
                        try:
                            raw = func(code, self.start_date, self.end_date, ktype=getattr(self, 'ktype', None))
                        except TypeError:
                            try:
                                raw = func(code, start=self.start_date, end=self.end_date, ktype=getattr(self, 'ktype', None))
                            except TypeError:
                                raw = func(code, self.start_date, self.end_date)
                        if raw is None or len(raw) == 0:
                            continue
                        dfp = pd.DataFrame(raw)
                        # 寻找收盘价列
                        for col in ('close', 'close_price', '收盘', 'close_px', 'closePrice'):
                            if col in dfp.columns:
                                if 'date' in dfp.columns:
                                    idx_dates = pd.to_datetime(dfp['date'])
                                elif 'trade_date' in dfp.columns:
                                    idx_dates = pd.to_datetime(dfp['trade_date'])
                                else:
                                    idx_dates = pd.to_datetime(dfp.index)
                                series = pd.Series(dfp[col].values, index=idx_dates).sort_index()
                                return series
                    except Exception:
                        continue
            return None

        # 为避免重复 IO，缓存每只股票的 close 序列
        close_cache = {}
        for code in codes:
            s = _fetch_close_series(code)
            if s is not None:
                # 只保留我们关心的交易日索引，保证对齐
                close_cache[code] = s.reindex(trade_dates)

        # 根据缓存计算 forward return 并合并回主表
        profit_frames = []
        suspension_frames = []  # 用于标记停牌状态
        
        for code, s in close_cache.items():
            # 识别停牌：当日有收盘价，但未来N日内任意一日价格缺失
            # 停牌标记：1=停牌（当日或未来N日内有缺失），0=正常交易
            is_suspended = pd.Series(False, index=s.index)
            
            # 检查当日是否有价格
            is_suspended |= s.isna()
            
            # 检查未来N日内是否有价格缺失（前视检查）
            for i in range(1, n + 1):
                is_suspended |= s.shift(-i).isna()
            
            # 未来 N 日收益： (close_{t+N} / close_t) - 1
            profit = (s.shift(-n) / s - 1).rename('profit')
            
            tmp = profit.reset_index()
            tmp.columns = ['date', 'profit']
            tmp['code'] = code
            profit_frames.append(tmp[['code', 'date', 'profit']])
            
            # 保存停牌标记
            tmp_susp = is_suspended.reset_index()
            tmp_susp.columns = ['date', 'is_suspended']
            tmp_susp['code'] = code
            suspension_frames.append(tmp_susp[['code', 'date', 'is_suspended']])

        if profit_frames:
            df_profit = pd.concat(profit_frames, ignore_index=True)
            df_profit['date'] = pd.to_datetime(df_profit['date'])
            df = df.merge(df_profit, on=['code', 'date'], how='left')
        else:
            df['profit'] = np.nan
            
        # 合并停牌标记
        if suspension_frames:
            df_suspension = pd.concat(suspension_frames, ignore_index=True)
            df_suspension['date'] = pd.to_datetime(df_suspension['date'])
            df = df.merge(df_suspension, on=['code', 'date'], how='left')
            df['is_suspended'] = df['is_suspended'].fillna(False)
        else:
            df['is_suspended'] = False

        # 数据清洗选项（通过参数控制）
        handle_suspension = getattr(self, 'handle_suspension', 'exclude')  # 'exclude', 'keep', 'forward_fill'
        
        if handle_suspension == 'exclude':
            # 方案1：排除停牌样本（推荐用于RankIC计算）
            before_filter = len(df)
            df = df[~df['is_suspended']].copy()
            after_filter = len(df)
            print(f"停牌处理：排除模式 - 过滤掉 {before_filter - after_filter} 条停牌记录")
            
        elif handle_suspension == 'forward_fill':
            # 方案2：用最后一个有效价格填充（谨慎使用）
            print("停牌处理：前向填充模式 - 使用最后有效价格填充停牌期收益")
            for code in codes:
                mask = (df['code'] == code)
                df.loc[mask, 'profit'] = df.loc[mask, 'profit'].fillna(method='ffill')
                
        else:  # 'keep'
            # 方案3：保留所有数据（包含NaN）
            print("停牌处理：保留模式 - 保留所有数据（含停牌NaN）")

        # 最终保存并返回
        self.prepared_data = df
        
        # 统计信息
        total_rows = len(df)
        factor_na = df['factor_flow_pct'].isna().sum()
        profit_na = df['profit'].isna().sum()
        suspended_count = df['is_suspended'].sum() if 'is_suspended' in df.columns else 0
        
        print(f"\n{'='*60}")
        print(f"数据准备完成:")
        print(f"  总记录数: {total_rows:,}")
        print(f"  因子缺失: {factor_na:,} ({factor_na/total_rows*100:.2f}%)")
        print(f"  收益缺失: {profit_na:,} ({profit_na/total_rows*100:.2f}%)")
        print(f"  停牌标记: {suspended_count:,} ({suspended_count/total_rows*100:.2f}%)" if handle_suspension != 'exclude' else "  停牌记录: 已排除")
        print(f"  有效样本: {(~df['factor_flow_pct'].isna() & ~df['profit'].isna()).sum():,}")
        print(f"{'='*60}\n")
        
        return df

    def prepare_single_data(
            self, 
            code: str = '000001.SZ', 
            start_date=None, 
            end_date=None, 
            n_days: int = 5, 
            mode: Literal['close', 'open'] = 'close'
        ) -> pd.DataFrame:
        """准备单只股票的数据,供IC与ICIR计算使用。
        
        Args:
            code: 股票代码，默认为 '000001.SZ'。
            start_date: 开始日期，默认为None，将使用实例的start_date。
            end_date: 结束日期，默认为None，将使用实例的end_date。
            n_days: 未来收益率的计算天数，默认为5。
            mode: 收益率计算模式，可选:
                'close': 默认值 基于当前收盘价和未来n_days的收盘价计算
                'open': 基于下一交易日开盘价和未来n_days的收盘价计算
                
        Returns:
            包含日期、价格和收益率的DataFrame。
            
        Raises:
            ValueError: 当mode参数不是'close'或'open'时抛出。
        """
        self.code = code
        # 获取单代码所有的日线数据
        df_1d = self.get_k_data()
        # 复制一份数据，准备进行收益率计算
        df_copy = df_1d.copy()
        # 使用 shift(-n_days) 获取未来第N个交易日的日期
        df_copy['end_date'] = df_copy['date'].shift(-n_days)
        if mode == 'close':
            # 计算收益率：基于当前日期和未来第N个交易日的收盘价
            # 将未来第N日的收盘价向前对齐到当前日期
            df_copy['future_close'] = df_copy['close'].shift(-n_days)
            # 计算收益率: (未来收盘价 / 当前收盘价) - 1
            df_copy['return'] = df_copy['future_close'] / df_copy['close'] - 1
        elif mode == 'open':
            # 计算收益率：基于下一交易日开盘价和未来第N个交易日的收盘价
            df_copy['next_open'] = df_copy['open'].shift(-1)
            df_copy['future_close'] = df_copy['close'].shift(-n_days)
            # 计算收益率: (未来收盘价 / 下一交易日开盘价) - 1
            df_copy['return'] = df_copy['future_close'] / df_copy['next_open'] - 1
        else:
            raise ValueError("mode 参数必须是 'close' 或 'open'")
        # 删除收益率为空的行（表示未来N日内无有效收盘价）
        df_copy = df_copy[df_copy['return'].notna()]
        # 删除end_date为空的行（表示未来N日内无交易数据）

        df_copy = df_copy[df_copy['end_date'].notna()]
        #print(df_copy)
        return df_copy
    
    def demo_IC资金流向演示(self, code = '000001.SZ'):
        """
        演示如何计算基于资金流向因子的单代码IC、ICIR、RankIC和RankICIR
        默认使用未来5日收益率计算
        
        RankIC (斯皮尔曼秩相关系数): 衡量因子排名与未来收益排名之间的相关性
        RankICIR: RankIC的均值/标准差，衡量RankIC的稳定性
        """
        # 获取收益率数据
        df_return = self.prepare_single_data(code, n_days=5, mode='close')[['date', 'end_date', 'return']]
        # 获取因子数据
        df_factor = pd.read_sql(f"SELECT date, volatility FROM stock_money_flow WHERE code = '{code}' and date between '{self.start_date}' and '{self.end_date}'", self.engine)
        # 合并数据
        df_merged = pd.merge(df_return, df_factor, on='date', how='inner')
        # 剔除因子或收益率为空的行
        df_merged = df_merged.dropna(subset=['volatility', 'return'])
        
        if len(df_merged) < 2:
            print(f"警告: {code} 的有效数据少于2条，无法计算相关性")
            return
        
        # 1. 计算普通IC (皮尔逊相关系数)
        # 按日期分组计算相关系数
        ic_daily = df_merged['volatility'].corr(df_merged['return'])
        
        # 2. 计算RankIC (斯皮尔曼秩相关系数)
        # 将因子值和收益率转换为排名
        df_merged['factor_rank'] = df_merged['volatility'].rank()
        df_merged['return_rank'] = df_merged['return'].rank()
        # 计算排名相关性
        rankic_daily = df_merged['factor_rank'].corr(df_merged['return_rank'], method='spearman')
        
        # 计算IC时序序列 - 按交易日计算
        ic_series = []
        rankic_series = []
        
        # 按日期分组，如果数据量足够，最好按每个交易日计算IC
        dates = df_merged['date'].unique()
        for date in dates:
            daily_data = df_merged[df_merged['date'] == date]
            if len(daily_data) > 2:  # 需要至少3个数据点来计算有意义的相关系数
                try:
                    # 计算日度IC
                    ic = daily_data['volatility'].corr(daily_data['return'])
                    ic_series.append({'date': date, 'IC': ic})
                    
                    # 计算日度RankIC
                    rankic = daily_data['volatility'].corr(daily_data['return'], method='spearman')
                    rankic_series.append({'date': date, 'RankIC': rankic})
                except Exception as e:
                    print(f"计算日期 {date} 的IC/RankIC时出错: {e}")
        
        # 转换为DataFrame
        if ic_series:
            df_ic = pd.DataFrame(ic_series)
            ic_mean = df_ic['IC'].mean()
            ic_std = df_ic['IC'].std()
            icir = ic_mean / ic_std if ic_std != 0 else 0
        else:
            ic_mean = ic_daily
            icir = 0
            
        if rankic_series:
            df_rankic = pd.DataFrame(rankic_series)
            rankic_mean = df_rankic['RankIC'].mean()
            rankic_std = df_rankic['RankIC'].std()
            rankicir = rankic_mean / rankic_std if rankic_std != 0 else 0
        else:
            rankic_mean = rankic_daily
            rankicir = 0
        
        # 输出结果
        print(f"\n{'=' * 60}")
        print(f"📊 股票代码: {code} 的因子有效性分析")
        print(f"{'=' * 60}")
        print(f"样本数量: {len(df_merged):,} 条")
        print(f"样本区间: {df_merged['date'].min()} 至 {df_merged['date'].max()}")
        print(f"时序IC数据点: {len(ic_series)} 个交易日" if ic_series else "时序IC数据点: 0（单点相关性）")
        print(f"\n1. 普通IC分析 (皮尔逊相关系数)")
        print(f"   IC均值: {ic_mean:.4f}")
        if ic_series:
            print(f"   IC标准差: {ic_std:.4f}")
            print(f"   ICIR: {icir:.4f}")
            print(f"   IC>0占比: {(df_ic['IC'] > 0).mean():.2%}")
            
        print(f"\n2. RankIC分析 (斯皮尔曼秩相关系数)")
        print(f"   RankIC均值: {rankic_mean:.4f}")
        if rankic_series:
            print(f"   RankIC标准差: {rankic_std:.4f}")
            print(f"   RankICIR: {rankicir:.4f}")
            print(f"   RankIC>0占比: {(df_rankic['RankIC'] > 0).mean():.2%}")
            
        print(f"\n3. 因子有效性评估")
        
        # 评估RankIC
        if abs(rankic_mean) < 0.02:
            rank_eval = "极弱"
        elif abs(rankic_mean) < 0.03:
            rank_eval = "微弱"
        elif abs(rankic_mean) < 0.06:
            rank_eval = "尚可"
        elif abs(rankic_mean) < 0.1:
            rank_eval = "良好" 
        else:
            rank_eval = "优秀"
            
        # 评估RankICIR
        if rankic_series:
            if abs(rankicir) < 0.5:
                rankicir_eval = "不稳定"
            elif abs(rankicir) < 0.8:
                rankicir_eval = "可用"
            elif abs(rankicir) < 1.0:
                rankicir_eval = "较好"
            else:
                rankicir_eval = "优秀"
            
            print(f"   因子预测能力: {rank_eval} (|RankIC均值|={abs(rankic_mean):.4f})")
            print(f"   因子稳定性: {rankicir_eval} (|RankICIR|={abs(rankicir):.4f})")
            
        # 如果有足够的时序数据，绘制IC走势图
        if len(ic_series) >= 10:
            try:
                import matplotlib
                import matplotlib.pyplot as plt
                
                # 可选：使用非交互式后端（避免弹窗）
                # matplotlib.use('Agg')  # 取消注释以保存图片而不显示
                
                plt.figure(figsize=(12, 6))
                plt.subplot(2, 1, 1)
                plt.plot(df_ic['date'], df_ic['IC'], 'b-', label='IC')
                plt.axhline(y=0, color='r', linestyle='--', alpha=0.5)
                plt.title(f'{code} IC时序图')
                plt.xlabel('日期')
                plt.ylabel('IC值')
                plt.legend()
                plt.grid(True, alpha=0.3)
                
                plt.subplot(2, 1, 2)
                plt.plot(df_rankic['date'], df_rankic['RankIC'], 'g-', label='RankIC')
                plt.axhline(y=0, color='r', linestyle='--', alpha=0.5)
                plt.title(f'{code} RankIC时序图')
                plt.xlabel('日期')
                plt.ylabel('RankIC值')
                plt.legend()
                plt.grid(True, alpha=0.3)
                
                plt.tight_layout()
                
                # 选项1: 显示图表（交互式）
                plt.show()
                
                # 选项2: 保存到文件（取消下面两行注释以启用）
                # plt.savefig(f'IC_analysis_{code}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png', dpi=300, bbox_inches='tight')
                # print(f"图表已保存到: IC_analysis_{code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                
            except Exception as e:
                print(f"绘图出错: {e}")

    

if __name__ == "__main__":
    # 初始化数据
    data = RankIC()  # 这里传入实际的数据
    data.start_date = datetime(2024, 1, 1)
    data.end_date = datetime(2025, 9, 30)
    data.ktype = '1d'
    n_days = 5  # 计算未来5日收益率
    data.demo_IC资金流向演示('301120.SZ')
    #data.prepare_single_data('688256.SH', data.start_date, data.end_date, n_days, mode='open')


    
    """
    停牌处理建议：
    1. 对于全市场股票池，停牌是常见现象，必须妥善处理
    2. 推荐使用 'exclude' 模式，虽然会减少样本，但结果更可靠
    3. 如果样本量过少，可以考虑：
       - 缩短持有期（减小N值）
       - 分市场环境分析（牛市停牌少，熊市停牌多）
       - 增加时间跨度以获得更多有效样本
    
    全市场股票代码示例：
     code  symbol   name market   list_date
     000001.SZ  000001   平安银行     主板  1991-04-03
     000002.SZ  000002    万科A     主板  1991-01-29
     000004.SZ  000004  *ST国华     主板  1991-01-14
     000006.SZ  000006   深振业A     主板  1992-04-27
     000007.SZ  000007    全新好     主板  1992-04-13
     [5437 rows x 5 columns]
    """
    
