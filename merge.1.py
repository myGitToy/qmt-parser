# -*- coding: utf-8 -*-
import pandas as pd
import tushare as ts 
#####读取最新的日线数据
new=ts.get_k_data('510050',ktype='60',autype='qfq')
new.to_csv('D:\\510050.csv')
print('新获取的数据量',len(new.index))

####第一次读取
stock1=pd.read_csv('D:\\510050.csv')
#stock1=ts.get_k_data('510050',ktype='60',autype='qfq')
#stock1=stock1[['date','open','close','high','low','volume','code']]
#stock1.set_index(['date'], inplace = True)
print('stock1数据量：',len(stock1.index))
#stock2=pd.read_csv('D:\\510050.csv')

####第二次读取
stock2=ts.get_k_data('510050',ktype='60',autype='qfq')
#stock2=ts.get_k_data('510050',ktype='60',autype='qfq')
#stock2=stock2[['date','open','close','high','low','volume','code']]
#stock2.set_index(['date'], inplace = True)
print('stock2数据量：',len(stock2.index))

####合并
stock=pd.concat([stock1, stock2])
stock=stock[['date','open','close','high','low','volume','code']]
print('合并未去重后的数据量：',len(stock.index))
stock.set_index(['date'], inplace = True)
stock=stock.drop_duplicates('date', 'first', inplace=True)
print('去重后的数据量：',len(stock.index))
print(stock)

#stock = stock.sort_values(by='date')
#stock=stock[['date','open','close','high','low','volume','code']]
#stock.set_index(['date'], inplace = True) 
#print(stock)

#stock_new = stock.drop_duplicates(subset = 'date', keep = 'last')
#stock_new = stock.drop_duplicates()
#stock_new=stock_new.sort_index(ascending =True)
#print("合并后的数据量：",len(stock_new.index))
#stock_new.to_csv('D:\\510050.csv')
