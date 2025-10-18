"""
Akshare 修复版接口集合
主要用来修复ak频繁封接口的问题，现在通过环境变量 EASTMONEY_COOKIES 传入 cookies来尝试绕过封禁
"""


from __future__ import annotations

import os
from typing import Optional

import pandas as pd
import requests


def _env_cookies_dict(env_var: str = "EASTMONEY_COOKIES") -> Optional[dict]:
    """
    从 cookies.py 强制获取 cookies 并转换为字典
    按照 fixed_stock_zh_a_hist 的思路处理 cookies
    """
    cookies_str = ""
    
    # 强制从 cookies.py 获取 cookies
    try:
        from apt.vendor.akshare.cookies import ensure_eastmoney_cookies_from_stock_page
        cookies_str = ensure_eastmoney_cookies_from_stock_page(force_refresh=False)
    except Exception:
        # 如果获取失败，返回 None
        return None
    
    if not cookies_str:
        return None
    
    # 将 cookies 字符串转换为字典（与 fixed_stock_zh_a_hist 保持一致）
    cookies_dict: dict[str, str] = {}
    for cookie in cookies_str.split(';'):
        if '=' in cookie:
            key, value = cookie.strip().split('=', 1)
            cookies_dict[key] = value
    
    return cookies_dict if cookies_dict else None


def fixed_stock_zh_a_hist_min_em(
    symbol: str = "000001",
    start_date: str = "1979-09-01 09:32:00",
    end_date: str = "2222-01-01 09:32:00",
    period: str = "1",
    adjust: str = "",
    timeout: Optional[float] = None,
) -> pd.DataFrame:
    """
    stock_zh_a_hist_min_em 的带 cookies 版本；从环境变量 EASTMONEY_COOKIES 读取。
    与 akshare 返回结构保持一致。
    """
    # 市场代码：上证=1（代码以6开头），深证=0
    market_code = 1 if symbol.startswith("6") else 0
    adjust_map = {"": "0", "qfq": "1", "hfq": "2"}
    # 兼容 '1m'/'5m' 等别名
    alias = {"1m": "1", "5m": "5", "15m": "15", "30m": "30", "60m": "60"}
    klt = alias.get(period, period)

    cookies = _env_cookies_dict()

    if klt == "1":
        url = "https://push2his.eastmoney.com/api/qt/stock/trends2/get"
        params = {
            "fields1": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
            "ut": "7eea3edcaed734bea9cbfc24409ed989",
            "ndays": "5",
            "iscr": "0",
            "secid": f"{market_code}.{symbol}",
            "_": "1623766962675",
        }
        r = requests.get(url, params=params, timeout=timeout, cookies=cookies)
        data_json = r.json()
        if not (data_json.get("data") and data_json["data"].get("trends")):
            return pd.DataFrame()
        temp_df = pd.DataFrame([item.split(",") for item in data_json["data"]["trends"]])
        temp_df.columns = ["时间", "开盘", "收盘", "最高", "最低", "成交量", "成交额", "最新价"]
        temp_df.index = pd.to_datetime(temp_df["时间"], errors="coerce")
        try:
            temp_df = temp_df[start_date:end_date]
        except Exception:
            pass
        temp_df.reset_index(drop=True, inplace=True)
        for col in ["开盘", "收盘", "最高", "最低", "成交量", "成交额", "最新价"]:
            temp_df[col] = pd.to_numeric(temp_df[col], errors="coerce")
        temp_df["时间"] = pd.to_datetime(temp_df["时间"], errors="coerce").astype(str)
        return temp_df
    else:
        url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        params = {
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "ut": "7eea3edcaed734bea9cbfc24409ed989",
            "klt": klt,
            "fqt": adjust_map.get(adjust, "0"),
            "secid": f"{market_code}.{symbol}",
            "beg": "0",
            "end": "20500000",
            "_": "1630930917857",
        }
        r = requests.get(url, params=params, timeout=timeout, cookies=cookies)
        data_json = r.json()
        if not (data_json.get("data") and data_json["data"].get("klines")):
            return pd.DataFrame()
        temp_df = pd.DataFrame([item.split(",") for item in data_json["data"]["klines"]])
        temp_df.columns = [
            "时间",
            "开盘",
            "收盘",
            "最高",
            "最低",
            "成交量",
            "成交额",
            "振幅",
            "涨跌幅",
            "涨跌额",
            "换手率",
        ]
        temp_df.index = pd.to_datetime(temp_df["时间"], errors="coerce")
        try:
            temp_df = temp_df[start_date:end_date]
        except Exception:
            pass
        temp_df.reset_index(drop=True, inplace=True)
        for col in ["开盘", "收盘", "最高", "最低", "成交量", "成交额", "振幅", "涨跌幅", "涨跌额", "换手率"]:
            temp_df[col] = pd.to_numeric(temp_df[col], errors="coerce")
        temp_df["时间"] = pd.to_datetime(temp_df["时间"], errors="coerce").astype(str)
        temp_df = temp_df[[
            "时间","开盘","收盘","最高","最低","涨跌幅","涨跌额","成交量","成交额","振幅","换手率"
        ]]
        return temp_df


def fixed_fund_etf_hist_min_em(
    symbol: str = "159707",
    start_date: str = "1979-09-01 09:32:00",
    end_date: str = "2222-01-01 09:32:00",
    period: str = "5",
    adjust: str = "",
    timeout: Optional[float] = None,
) -> pd.DataFrame:
    """
    fund_etf_hist_min_em 的带 cookies 版本；从环境变量 EASTMONEY_COOKIES 读取。
    与 akshare 返回结构保持一致。
    """
    # ETF 市场代码映射（东财 ETF 使用 secid: {market}.{code}，一般 0/1，ETF 多为深市0或沪市1），
    market_code = 1 if symbol.startswith("5") and not symbol.startswith("159") else 0
    adjust_map = {"": "0", "qfq": "1", "hfq": "2"}
    alias = {"1m": "1", "5m": "5", "15m": "15", "30m": "30", "60m": "60"}
    klt = alias.get(period, period)

    cookies = _env_cookies_dict()

    if klt == "1":
        url = "https://push2his.eastmoney.com/api/qt/stock/trends2/get"
        params = {
            "fields1": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
            "ut": "7eea3edcaed734bea9cbfc24409ed989",
            "ndays": "5",
            "iscr": "0",
            "secid": f"{market_code}.{symbol}",
            "_": "1623766962675",
        }
        r = requests.get(url, params=params, timeout=timeout, cookies=cookies)
        data_json = r.json()
        if not (data_json.get("data") and data_json["data"].get("trends")):
            return pd.DataFrame()
        temp_df = pd.DataFrame([item.split(",") for item in data_json["data"]["trends"]])
        temp_df.columns = ["时间", "开盘", "收盘", "最高", "最低", "成交量", "成交额", "最新价"]
        temp_df.index = pd.to_datetime(temp_df["时间"], errors="coerce")
        try:
            temp_df = temp_df[start_date:end_date]
        except Exception:
            pass
        temp_df.reset_index(drop=True, inplace=True)
        for col in ["开盘", "收盘", "最高", "最低", "成交量", "成交额", "最新价"]:
            temp_df[col] = pd.to_numeric(temp_df[col], errors="coerce")
        temp_df["时间"] = pd.to_datetime(temp_df["时间"], errors="coerce").astype(str)
        return temp_df
    else:
        url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        params = {
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "ut": "7eea3edcaed734bea9cbfc24409ed989",
            "klt": klt,
            "fqt": adjust_map.get(adjust, "0"),
            "secid": f"{market_code}.{symbol}",
            "beg": "0",
            "end": "20500000",
            "_": "1630930917857",
        }
        r = requests.get(url, params=params, timeout=timeout, cookies=cookies)
        data_json = r.json()
        if not (data_json.get("data") and data_json["data"].get("klines")):
            return pd.DataFrame()
        temp_df = pd.DataFrame([item.split(",") for item in data_json["data"]["klines"]])
        temp_df.columns = [
            "时间",
            "开盘",
            "收盘",
            "最高",
            "最低",
            "成交量",
            "成交额",
            "振幅",
            "涨跌幅",
            "涨跌额",
            "换手率",
        ]
        temp_df.index = pd.to_datetime(temp_df["时间"], errors="coerce")
        try:
            temp_df = temp_df[start_date:end_date]
        except Exception:
            pass
        temp_df.reset_index(drop=True, inplace=True)
        for col in ["开盘", "收盘", "最高", "最低", "成交量", "成交额", "振幅", "涨跌幅", "涨跌额", "换手率"]:
            temp_df[col] = pd.to_numeric(temp_df[col], errors="coerce")
        temp_df["时间"] = pd.to_datetime(temp_df["时间"], errors="coerce").astype(str)
        temp_df = temp_df[[
            "时间","开盘","收盘","最高","最低","涨跌幅","涨跌额","成交量","成交额","振幅","换手率"
        ]]
        return temp_df
    
if __name__ == "__main__":
    
    
    
    df = fixed_stock_zh_a_hist_min_em(symbol="000001", period="1", start_date="2025-10-01 09:30:00", end_date="2025-10-18 15:00:00")
    print(df)
