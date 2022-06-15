import akshare as ak
import pandas as pd
# 列名与数据对其显示
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
# 显示所有列
pd.set_option('display.max_columns', None)
# 显示所有行
pd.set_option('display.max_rows', None)

#实时数据接口
#ak.stock_zh_a_spot() 


#获取A股历史日线数据 
#使用601012 2022/6/6 复权前后的数据，不复权数据校验通过
stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol="601012", period="daily", start_date="20220608", end_date='20220705' ,adjust = '')
print(stock_zh_a_hist_df)


#获取复权因子（后复权 且非每日复权因子，只在复权日有因子数据）
#后复权因子和jpdata类似，但是ak的后复权以1900年为起始点，jadata以2005为起点，因此两者复权因子有区别
#复权因子校验与jadata相同，隆基2012上市，也会输出1900年的数据，数据拼接时需要注意
"""
         date           hfq_factor
0  2022-06-06  19.2302708477639000
.......
11 2012-06-26   1.8160237388724000
12 2012-04-11   1.0000000000000000
13 1900-01-01   1.0000000000000000
"""
hfq_factor_df = ak.stock_zh_a_daily(symbol="sh600038", adjust="hfq-factor")
print(hfq_factor_df)


#获取A股历史日线数据
#163数据源（可获取全部数据 不含权）
#stock_zh_a_hist_163_df = ak.stock_zh_a_hist_163(symbol="sh601012", start_date="20000101", end_date="20221201")
#print(stock_zh_a_hist_163_df)

#获取场内基金日线数据（只有日线和收盘价 且非OHCL数据）
fund_etf_fund_info_em_df = ak.fund_etf_fund_info_em(fund="159949", start_date="20200101", end_date="20220609")
print(fund_etf_fund_info_em_df)


#获取分时数据（1分钟的话保留约7天的数据）
#stock_zh_a_hist_min_em_df = ak.stock_zh_a_hist_min_em(symbol="000001", start_date="2021-05-01 09:32:00", end_date="2022-09-06 09:32:00", period='30', adjust='')
#print(stock_zh_a_hist_min_em_df)


#获取分笔数据 163（只能返回最近5天的数据，且目前无法获取上交所数据）
#stock_zh_a_tick_163_df = ak.stock_zh_a_tick_163(symbol="sz000001", trade_date="20220507")
#print(stock_zh_a_tick_163_df)


#获取分笔数据 腾讯（目前该接口无法使用）
#stock_zh_a_tick_tx_df = ak.stock_zh_a_tick_tx(symbol="sz000001", trade_date="20220607")
#print(stock_zh_a_tick_tx_df)