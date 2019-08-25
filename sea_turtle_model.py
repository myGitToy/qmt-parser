# -*- coding: utf-8 -*-
'''
[海龟模型]######
函数说明 乔晖 2018/3/30
通过检查[ags_snapshot]
'''
import tushare as ts
import pandas as pd
#获取K线数据
'''
各档数据接口说明：
get_k_data：获取最新数据，接口最快最稳定，但数据时间跨度不长，仅提供最新的640条左右
            使用规范：ts.get_k_data('510300')
            ts.get_k_data('510300', start='2018-02-21',end='2018-01-01',ktype='60',autype='qfq')

get_hist_data：以前比较常用的接口数据，三年以上的数据不提供
            使用规范：ts.get_hist_data('600848',start='2015-01-05',end='2015-02-09')
            
s.get_h_data：历史数据，范围长，但不提供指数基金数据，比如510300
            使用规范：ts.get_h_data('510300', start='2017-01-01', end='2017-03-16')
            
'''
#df = ts.get_k_data('510300')
df = ts.get_k_data('510050', start='2014-02-21',end='2015-03-01',ktype='D',autype='qfq')  #work
#df=ts.get_h_data('600848', start='2012-01-01', end='2012-03-16')  #work only with normal code, na for 510300
#df=ts.get_hist_data('600848',start='2015-01-05',end='2015-02-09')
print(df)
df.to_csv('~/environment/TuShare/data/day/510300.csv')
#将索引更改为日期
df = df.set_index('date', drop = False)

#df= df.reset_index()
#重定义各列名，为df的聚合做准备
df.columns = ['date','open','close','high','low','volume','code']
##获取10日均线数据，返回值为sieres
df_ma10=df['close'].rolling(10).mean()
#sieres变更为dateframe并重置列名
df_ma10 = df_ma10.to_frame().reset_index()
#重新定义列名
df_ma10.columns = ['date','ma10']
########END########

########获取100日均线数据，返回值为sieres
df_ma100=df['close'].rolling(100).mean()
#sieres变更为dateframe并重置列名
df_ma100 = df_ma100.to_frame().reset_index()
#重新定义列名
df_ma100.columns = ['date','ma100']
########END########

########获取50日最大值，返回值为sieres
df_max50=df['high'].rolling(50).max()
#sieres变更为dateframe并重置列名
df_max50 = df_max50.to_frame().reset_index()
#重新定义列名
df_max50.columns = ['date','max50']
########END########

########获取50日最小值，返回值为sieres
df_min50=df['low'].rolling(50).min()
#sieres变更为dateframe并重置列名
df_min50 = df_min50.to_frame().reset_index()
#重新定义列名
df_min50.columns = ['date','min50']
########END########

########获取25日最小值，返回值为sieres
df_min25=df['low'].rolling(25).min()
#sieres变更为dateframe并重置列名
df_min25 = df_min25.to_frame().reset_index()
#重新定义列名
df_min25.columns = ['date','min25']
########END########
print(df.head(10))
#print(df_ma10.head(10))
#数据聚合，以时间为索引
df_new=pd.merge(df,df_ma10, how='inner',on = ['date'])
df_new=pd.merge(df_new,df_ma100, how='inner',on = ['date'])
df_new=pd.merge(df_new,df_max50, how='inner',on = ['date'])
df_new=pd.merge(df_new,df_min50, how='inner',on = ['date'])
df_new=pd.merge(df_new,df_min25, how='inner',on = ['date'])
df_new.to_csv('~/environment/TuShare/data/day/510050.csv')
print(df_new)