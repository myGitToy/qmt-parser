from jqdatasdk import *
import pandas as pd
import datetime
#显示所有列
pd.set_option('display.max_columns', None)
auth('13817092632','JQ@tushare123')
#行情基础数据（含复权数据）
#df = get_price(security = '512760.XSHG',end_date='2020-11-20' ,count = 100 ,frequency='1d',fields=['open', 'close', 'high', 'low', 'volume', 'money','factor'], skip_paused=True, fq=None,  fill_paused=False)
#start_date 不是必须，end_date必须要有（不填写，默认是2015年的，所以会导致返回空值）
#关于列：
    #1d 列：['open', 'close', 'high', 'low', 'volume', 'money','paused','factor']
    #5m 列：['open', 'close', 'high', 'low', 'volume', 'money']
#df = get_price(security = '512760.XSHG',start_date='2020-09-01' ,end_date = '2020-09-8',frequency='1d',fields=['open', 'close', 'high', 'low', 'volume', 'money','paused','factor'], skip_paused=True, fq='pre',  fill_paused=False)
day = datetime.datetime(2020,9,12)
df = get_bars(security = '512760.XSHG', count = 20, unit='60m',fields=['date', 'open', 'close', 'high', 'low', 'volume', 'money','factor'],include_now=False, end_dt= day, fq_ref_date=day,df=True)

"""
             open  close   high    low        volume         money    factor
2020-06-24  1.048  1.066  1.076  1.046  9.145897e+08  9.721797e+08  0.477323
2020-06-29  1.059  1.052  1.071  1.044  7.674453e+08  8.090507e+08  0.477323
2020-06-30  1.061  1.072  1.078  1.054  7.756317e+08  8.272044e+08  0.477323
2020-07-01  1.074  1.085  1.105  1.062  1.126561e+09  1.221893e+09  0.477323
2020-07-02  1.089  1.110  1.118  1.078  8.906166e+08  9.835169e+08  0.477323
          ...    ...    ...    ...           ...           ...       ...
2020-11-16  1.187  1.177  1.188  1.167  4.503166e+08  5.288154e+08  1.000000
2020-11-17  1.171  1.185  1.187  1.135  1.147316e+09  1.329366e+09  1.000000
2020-11-18  1.175  1.177  1.191  1.165  7.971829e+08  9.396277e+08  1.000000
2020-11-19  1.167  1.186  1.200  1.162  7.082886e+08  8.416416e+08  1.000000
2020-11-20  1.185  1.185  1.200  1.180  4.052624e+08  4.807744e+08  1.000000

[100 rows x 7 columns]
"""
#bar行情



#资金流向
#df = get_money_flow(['000001.XSHE'], '2020-10-01', '2020-11-15')
#获取龙虎榜数据    
#df = get_billboard_list(stock_list = ['000001.XSHE'], start_date = '2020-08-01', end_date = '2020-11-15')
#获取融资融券信息
#df = get_mtss('000001.XSHE', '2020-10-01', '2020-11-16')
df.to_csv('.\\data\\512760_jqdata.csv', encoding = 'utf_8_sig')
print(df)
#查询当日剩余可调用数据条数
count=get_query_count()
print(count)    