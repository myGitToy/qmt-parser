import akshare as ak
#机构调研-统计 记录详细信息
stock_jgdy_tj_em_df = ak.stock_jgdy_tj_em(date="20230301").query('接待机构数量 >20')
print(stock_jgdy_tj_em_df[['代码','名称','接待机构数量','接待日期','公告日期']])

#机构调研-详细 未汇总的全部信息
stock_jgdy_detail_em_df = ak.stock_jgdy_detail_em(date="20230301")
print(stock_jgdy_detail_em_df)