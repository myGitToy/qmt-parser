"""短期截面指标批量计算器

功能：
- 对一个股票池（dict of DataFrame）和大盘索引 DataFrame，计算每个标的在每个交易日的短期窗口指标（默认 7 日）。
- 输出每个指标的 panel（DataFrame: index=日期, columns=代码）以及对应的每日截面 z-score 矩阵。

使用说明：见 __main__ 中的示例（生成合成数据并运行 smoke test）。
"""
from typing import Dict, Tuple, List, Optional
import numpy as np
import pandas as pd


def _rsi(series: pd.Series, n: int = 5) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0).rolling(window=n, min_periods=1).mean()
    down = -delta.clip(upper=0).rolling(window=n, min_periods=1).mean()
    rs = up / (down.replace(0, np.nan))
    rsi = 100 - 100 / (1 + rs)
    return rsi


def compute_metrics_for_symbol(
    s: pd.Series,
    index_close: pd.Series,
    window: int = 7,
) -> pd.DataFrame:
    """计算单只股票在每个交易日可对齐的短期指标。

    返回：DataFrame，index 为日期，columns 为指标名（每日值，针对以该日为结尾的 window）。
    """
    df = pd.DataFrame({'close': s}).copy()
    df['ret'] = df['close'].pct_change()
    idx = pd.DataFrame({'index_close': index_close}).reindex(df.index)
    df['index_ret'] = idx['index_close'].pct_change()

    # rolling window aligned to right (window ending at current day)
    roll_ret = df['ret'].rolling(window=window, min_periods=1)
    roll_idx_ret = df['index_ret'].rolling(window=window, min_periods=1)

    # metrics
    df_metrics = pd.DataFrame(index=df.index)
    # cumulative return over window (from t-window to t)
    df_metrics['cum_return'] = df['close'] / df['close'].shift(window) - 1
    df_metrics['mean_daily_return'] = roll_ret.mean()
    df_metrics['std_daily_return'] = roll_ret.std()
    # realized vol (non-annualized)
    df_metrics['realized_vol'] = np.sqrt((roll_ret.apply(lambda x: np.sum(x**2))) / (window - 1 + 1e-12))
    # rolling beta: slope of linear regression vs index returns
    def _rolling_beta(x_ret, y_ret):
        if x_ret.size < 2:
            return np.nan
        A = np.vstack([y_ret, np.ones(len(y_ret))]).T
        try:
            slope = np.linalg.lstsq(A, x_ret, rcond=None)[0][0]
            return slope
        except Exception:
            return np.nan

    betas = []
    track_err = []
    corr = []
    for end in range(len(df)):
        start = max(0, end - window + 1)
        x = df['ret'].iloc[start:end+1].dropna()
        y = df['index_ret'].iloc[start:end+1].dropna()
        # align
        common = x.index.intersection(y.index)
        x = x.reindex(common)
        y = y.reindex(common)
        if len(x) < 2:
            betas.append(np.nan)
            track_err.append(np.nan)
            corr.append(np.nan)
        else:
            betas.append(_rolling_beta(x.values, y.values))
            track_err.append((x - y).std())
            corr.append(x.corr(y))

    df_metrics['beta'] = pd.Series(betas, index=df.index)
    df_metrics['tracking_error'] = pd.Series(track_err, index=df.index)
    df_metrics['rolling_corr'] = pd.Series(corr, index=df.index)

    # volume ratio if volume present
    # The caller can attach 'volume' column to series by passing a Series with name 'close' and using external volume.
    # Here we keep API simple: volume handled by outer loop if available.

    # RSI(5)
    df_metrics['rsi5'] = _rsi(df['close'], n=5)

    # win/lose streaks
    up = (df['ret'] > 0).astype(int)
    down = (df['ret'] < 0).astype(int)
    # compute consecutive days ending at t
    streak_up = up * (up.groupby((up != up.shift()).cumsum()).cumcount() + 1)
    streak_down = down * (down.groupby((down != down.shift()).cumsum()).cumcount() + 1)
    df_metrics['streak_up'] = streak_up
    df_metrics['streak_down'] = streak_down

    return df_metrics


def batch_compute_metrics(
    stock_data: Dict[str, pd.DataFrame],
    index_df: pd.DataFrame,
    window: int = 7,
    metrics_keep: Optional[List[str]] = None,
) -> Tuple[Dict[str, pd.DataFrame], Dict[str, pd.DataFrame]]:
    """对股票池批量计算指标。

    stock_data: dict(symbol -> DataFrame with at least 'close', optional 'volume')
    index_df: DataFrame with 'close' and datetime index

    返回：
      - metrics_panels: dict metric_name -> DataFrame(index=日期, columns=symbols)
      - zscores_panels: dict metric_name -> DataFrame(index=日期, columns=symbols) （每日截面 z-score）
    """
    symbols = list(stock_data.keys())
    # first, determine global date index (union of all dates present) - we'll use intersection with index_df
    all_dates = None
    for sym, df in stock_data.items():
        if all_dates is None:
            all_dates = set(df.index)
        else:
            all_dates |= set(df.index)
    all_dates = pd.DatetimeIndex(sorted(all_dates)) if all_dates is not None else pd.DatetimeIndex([])
    # restrict to dates present in index_df
    common_dates = all_dates.intersection(index_df.index)

    # compute metrics per symbol
    per_symbol_metrics: Dict[str, pd.DataFrame] = {}
    for sym, df in stock_data.items():
        # ensure datetime index and sorted
        d = df.copy()
        d = d.sort_index()
        # use close series reindexed to common_dates to ensure alignment
        s_close = d['close'].reindex(common_dates)
        idx_close = index_df['close'].reindex(common_dates)
        per_symbol_metrics[sym] = compute_metrics_for_symbol(s_close, idx_close, window=window)
    # gather metric names
    metric_names = list(next(iter(per_symbol_metrics.values())).columns)
    if metrics_keep is not None:
        metric_names = [m for m in metric_names if m in metrics_keep]

    # build panels
    metrics_panels: Dict[str, pd.DataFrame] = {}
    for m in metric_names:
        panels = {sym: per_symbol_metrics[sym][m] for sym in symbols}
        metrics_panels[m] = pd.DataFrame(panels)

    # compute daily cross-sectional z-score for each metric
    zscores_panels: Dict[str, pd.DataFrame] = {}
    for m, panel in metrics_panels.items():
        # cross-sectional mean/std for each date (axis=1)
        mean = panel.mean(axis=1)
        std = panel.std(axis=1).replace(0, np.nan)
        z = (panel.sub(mean, axis=0)).div(std, axis=0)
        zscores_panels[m] = z

    return metrics_panels, zscores_panels


if __name__ == '__main__':
    # quick smoke test with synthetic data
    import os
    print('running short_term_metrics self-test...')
    np.random.seed(42)
    dates = pd.bdate_range(end=pd.Timestamp.today(), periods=60)
    symbols = [f'SYM{i:03d}' for i in range(10)]
    stock_data = {}
    for s in symbols:
        # generate random walk with slight drift
        returns = np.random.normal(loc=0.0005, scale=0.02, size=len(dates))
        price = 100 * np.exp(np.cumsum(returns))
        df = pd.DataFrame({'close': price}, index=dates)
        stock_data[s] = df

    # market index with positive drift
    idx_returns = np.random.normal(loc=0.0007, scale=0.01, size=len(dates))
    idx_price = 3000 * np.exp(np.cumsum(idx_returns))
    index_df = pd.DataFrame({'close': idx_price}, index=dates)

    metrics, zscores = batch_compute_metrics(stock_data, index_df, window=7)
    # print a couple of heads
    for k in ['cum_return', 'beta', 'rsi5']:
        if k in metrics:
            print('\nMetric:', k)
            print(metrics[k].tail(5))
            print('\nZ-scores:')
            print(zscores[k].tail(5))
    # save a sample csv
    outdir = os.path.join(os.path.dirname(__file__), 'out_short_metrics')
    os.makedirs(outdir, exist_ok=True)
    metrics['cum_return'].to_csv(os.path.join(outdir, 'cum_return.csv'))
    zscores['cum_return'].to_csv(os.path.join(outdir, 'cum_return_z.csv'))
    print('\nself-test done, files written to', outdir)
