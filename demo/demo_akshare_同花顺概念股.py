"""
本模块用于演示同花顺概念股的获取和数据整合、拼接
"""
from apt.vendor.akshare.data import data as data
from apt.qsp_universal.base import base as qsp_base
from datetime import datetime
import pandas as pd
import akshare as ak
# 显示所有行
pd.set_option('display.max_rows', None)

#测试akshare数据获取模块
a = data()
a.start_date= datetime(2023,6,15,8)
a.end_date = datetime(2023,6,15,16)
a.ktype = '1m'
a.code = '601128.SH'


#print(ak.stock_board_industry_info_ths())

#同花顺概念板块-成分股
#stock_board_concept_info_ths = ak.stock_board_concept_info_ths(symbol = '牙科医疗')
#print(stock_board_concept_info_ths)
#stock_board_concept_info_ths.to_csv('.\\data\\同花顺概念股.csv', encoding = 'utf_8_sig')
#同花顺行业板块-成分股


#测试同花顺行业一览表（用于总体浏览）
#stock_board_industry_summary_ths_df = ak.stock_board_industry_summary_ths()
#print(stock_board_industry_summary_ths_df)
"""
名称	类型	描述
序号	int64	-
板块	object	-
涨跌幅	object	注意单位: %
总成交量	float64	注意单位: 万手
总成交额	float64	注意单位: 亿元
净流入	float64	注意单位: 亿元
上涨家数	float64	-
下跌家数	float64	-
均价	float64	-
领涨股	float64	-
领涨股-最新价	object	-
领涨股-涨跌幅	object	注意单位: %
"""


#同花顺-概念时间表
#限量: 单次返回当前所有概念时间表
stock_board_concept_name_ths_df = ak.stock_board_concept_name_ths()
#print(stock_board_concept_name_ths_df)
"""
日期	object	-
概念名称	object	-
成分股数量	int64	-
网址	object	-
代码	object	同花顺内部代码

             日期           概念名称 成分股数量                                             网址      代码
0    2023-07-05          半年报预增    32  http://q.10jqka.com.cn/gn/detail/code/308458/  308458
1    2023-06-09           算力租赁    43  http://q.10jqka.com.cn/gn/detail/code/309068/  309068
2    2023-06-08           空间计算    28  http://q.10jqka.com.cn/gn/detail/code/309066/  309066
3    2023-05-29          英伟达概念    28  http://q.10jqka.com.cn/gn/detail/code/309065/  309065
4    2023-05-26           脑机接口    12  http://q.10jqka.com.cn/gn/detail/code/308535/  308535
5    2023-05-20       MR（混合现实）    27  http://q.10jqka.com.cn/gn/detail/code/309063/  309063
"""


#同花顺-成份股-概念名称
#接口: stock_board_concept_cons_ths
stock_board_cons_ths_df = ak.stock_board_cons_ths(symbol="309068")
print(stock_board_cons_ths_df)
"""
      序号      代码    名称      现价    涨跌幅    涨跌    涨速     换手    量比     振幅     成交额      流通股       流通市值     市盈率
0      1  300475  香农芯创   31.00  14.43  3.91  0.13  10.25  4.07  22.04  13.86亿    4.42亿   136.96亿   41.52
1      2  600410  华胜天成    7.68   5.06  0.37  0.13   7.07  1.91   6.57   5.85亿   10.96亿    84.21亿   34.30
2      3  601216  君正集团    4.30   4.37  0.18  0.00   1.21  6.45   5.83   4.36亿   84.38亿   362.83亿   10.93
3      4  301236  软通动力   28.55   4.01  1.10  0.00   4.39  1.49   7.03   7.06亿    5.67亿   161.89亿  112.15
"""

#概念列表和成分股拼接
ths_all = pd.DataFrame()
for list in stock_board_concept_name_ths_df['代码'][0:3]:
    #循环获取所有概念代码
    df = ak.stock_board_cons_ths(symbol = list)
    ths_all = pd.concat([ths_all, df] , ignore_index = True)
    print(ths_all)
              