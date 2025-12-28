import os
import pandas as pd
import requests
def fixed_stock_zh_a_hist(
    symbol: str = "000001",
    period: str = "daily",
    start_date: str = "19700101",
    end_date: str = "20500101",
    adjust: str = "",
    timeout: float = None,
) -> pd.DataFrame:
    """
    东方财富网-行情首页-沪深京 A 股-每日行情
    https://quote.eastmoney.com/concept/sh603777.html?from=classic
    :param symbol: 股票代码
    :type symbol: str
    :param period: choice of {'daily', 'weekly', 'monthly'}
    :type period: str
    :param start_date: 开始日期
    :type start_date: str
    :param end_date: 结束日期
    :type end_date: str
    :param adjust: choice of {"qfq": "前复权", "hfq": "后复权", "": "不复权"}
    :type adjust: str
    :param timeout: choice of None or a positive float number
    :type timeout: float
    :return: 每日行情
    :rtype: pandas.DataFrame
    """
    market_code = 1 if symbol.startswith("6") else 0
    adjust_dict = {"qfq": "1", "hfq": "2", "": "0"}
    period_dict = {"daily": "101", "weekly": "102", "monthly": "103"}
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116",
        "ut": "7eea3edcaed734bea9cbfc24409ed989",
        "klt": period_dict[period],
        "fqt": adjust_dict[adjust],
        "secid": f"{market_code}.{symbol}",
        "beg": start_date,
        "end": end_date,
    }
    # 从环境变量读取 cookies，变量名：EASTMONEY_COOKIES（形如 "key1=val1; key2=val2"）
    cookies_env = os.environ.get("EASTMONEY_COOKIES", "")
    if cookies_env:
        cookies_dict = {}
        for cookie in cookies_env.split(';'):
            if '=' in cookie:
                key, value = cookie.strip().split('=', 1)
                cookies_dict[key] = value
        r = requests.get(url, params=params, timeout=timeout, cookies=cookies_dict)
    else:
        r = requests.get(url, params=params, timeout=timeout)
    data_json = r.json()
    if not (data_json["data"] and data_json["data"]["klines"]):
        return pd.DataFrame()
    temp_df = pd.DataFrame([item.split(",") for item in data_json["data"]["klines"]])
    temp_df["股票代码"] = symbol
    temp_df.columns = [
        "日期",
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
        "股票代码",
    ]
    temp_df["日期"] = pd.to_datetime(temp_df["日期"], errors="coerce").dt.date
    temp_df["开盘"] = pd.to_numeric(temp_df["开盘"], errors="coerce")
    temp_df["收盘"] = pd.to_numeric(temp_df["收盘"], errors="coerce")
    temp_df["最高"] = pd.to_numeric(temp_df["最高"], errors="coerce")
    temp_df["最低"] = pd.to_numeric(temp_df["最低"], errors="coerce")
    temp_df["成交量"] = pd.to_numeric(temp_df["成交量"], errors="coerce")
    temp_df["成交额"] = pd.to_numeric(temp_df["成交额"], errors="coerce")
    temp_df["振幅"] = pd.to_numeric(temp_df["振幅"], errors="coerce")
    temp_df["涨跌幅"] = pd.to_numeric(temp_df["涨跌幅"], errors="coerce")
    temp_df["涨跌额"] = pd.to_numeric(temp_df["涨跌额"], errors="coerce")
    temp_df["换手率"] = pd.to_numeric(temp_df["换手率"], errors="coerce")
    temp_df = temp_df[
        [
            "日期",
            "股票代码",
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
    ]
    return temp_df


def fixed_stock_zh_a_hist_min_em(
    symbol: str = "000001",
    start_date: str = "1979-09-01 09:32:00",
    end_date: str = "2222-01-01 09:32:00",
    period: str = "5",
    adjust: str = "",
    timeout: float | None = None,
) -> pd.DataFrame:
    """
    东方财富网-行情首页-沪深京 A 股-每日分时行情（带 cookies 支持）
    尽量保持与 akshare 原始 `stock_zh_a_hist_min_em` 的行为一致：
    - 当 period == '1' 时，使用 trends2 接口，最多 5 日分时；返回列包含“最新价”
    - 否则使用 kline 接口；返回列包含 涨跌幅/涨跌额/振幅/换手率

    cookies 来源：环境变量 EASTMONEY_COOKIES（形如 "k1=v1; k2=v2"）
    """
    # 市场代码简化：6 开头为上证(1)，其余深证(0)
    market_code = 1 if symbol.startswith("6") else 0

    # 复权与周期映射
    adjust_map = {"": "0", "qfq": "1", "hfq": "2"}
    period_alias = {"1m": "1", "5m": "5", "15m": "15", "30m": "30", "60m": "60"}
    klt = period_alias.get(period, period)

    # cookies 环境变量解析
    cookies_env = os.environ.get("EASTMONEY_COOKIES", "")
    cookies_dict = None
    if cookies_env:
        cookies_dict = {}
        for cookie in cookies_env.split(";"):
            if "=" in cookie:
                key, value = cookie.strip().split("=", 1)
                cookies_dict[key] = value

    if klt == "1":
        # 1 分钟分时：trends2 接口，取回后用 start/end 过滤
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
        r = requests.get(url, params=params, timeout=timeout, cookies=cookies_dict)
        data_json = r.json()
        if not (data_json.get("data") and data_json["data"].get("trends")):
            return pd.DataFrame()
        temp_df = pd.DataFrame([item.split(",") for item in data_json["data"]["trends"]])
        temp_df.columns = [
            "时间",
            "开盘",
            "收盘",
            "最高",
            "最低",
            "成交量",
            "成交额",
            "最新价",
        ]
        temp_df.index = pd.to_datetime(temp_df["时间"], errors="coerce")
        # 时间过滤
        try:
            temp_df = temp_df[start_date:end_date]
        except Exception:
            pass
        temp_df.reset_index(drop=True, inplace=True)
        # 数值转换
        for col in ["开盘", "收盘", "最高", "最低", "成交量", "成交额", "最新价"]:
            temp_df[col] = pd.to_numeric(temp_df[col], errors="coerce")
        temp_df["时间"] = pd.to_datetime(temp_df["时间"], errors="coerce").astype(str)
        return temp_df
    else:
        # 5/15/30/60 分钟：kline 接口
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
        r = requests.get(url, params=params, timeout=timeout, cookies=cookies_dict)
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
        # 时间过滤
        try:
            temp_df = temp_df[start_date:end_date]
        except Exception:
            pass
        temp_df.reset_index(drop=True, inplace=True)
        # 数值转换
        for col in ["开盘", "收盘", "最高", "最低", "成交量", "成交额", "振幅", "涨跌幅", "涨跌额", "换手率"]:
            temp_df[col] = pd.to_numeric(temp_df[col], errors="coerce")
        temp_df["时间"] = pd.to_datetime(temp_df["时间"], errors="coerce").astype(str)
        # 列顺序与原版保持一致
        temp_df = temp_df[
            [
                "时间",
                "开盘",
                "收盘",
                "最高",
                "最低",
                "涨跌幅",
                "涨跌额",
                "成交量",
                "成交额",
                "振幅",
                "换手率",
            ]
        ]
        return temp_df

if __name__ == "__main__":
    # 测试代码
    df_daily = fixed_stock_zh_a_hist(
        symbol="000001",
        period="daily",
        start_date="20220101",
        end_date="20221231",
        adjust="qfq",
    )
    print(df_daily)

    df_min = fixed_stock_zh_a_hist_min_em(
        symbol="000001",
        start_date="2025-10-01 09:30:00",  
        end_date="2025-10-18 15:00:00",
        period="1",
        adjust="",  # Already set to empty string for no adjustment (不复权)
    )
    print(df_min)
