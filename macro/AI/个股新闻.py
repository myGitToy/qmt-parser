"""
个股新闻
接口: stock_news_em
20250710 issue修复老接口的问题，但是获取的新闻链接无法访问
"""
import akshare as ak
# 设置显示所有行和列
import pandas as pd
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

stock_news_em_df = ak.stock_news_em(symbol="600696")
print(stock_news_em_df)
# 数据存盘csv
stock_news_em_df.to_csv("stock_news_em.csv", index=False, encoding="utf-8-sig")

