"""
个股新闻
接口: stock_news_em
"""
import akshare as ak

stock_news_em_df = ak.stock_news_em(symbol="600696")
print(stock_news_em_df)