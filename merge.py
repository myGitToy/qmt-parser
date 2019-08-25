# -*- coding: utf-8 -*-
import pandas as pd
import tushare as ts 
print("hello world")
#stock=pd.read_csv('c:\\510050.csv')
stock1=pd.read_csv('D:\\510050.csv')
#stock1=ts.get_k_data('510050',ktype='60',autype='qfq')
stock1=stock1[['date','open','close','high','low','volume','code']]
stock1.set_index(['date'], inplace = True)
print("stock数据量：",len(stock1.index))
#stock2=pd.read_csv('D:\\510050.csv')
stock2=ts.get_k_data('510050',ktype='60',autype='qfq')
stock2=stock2[['date','open','close','high','low','volume','code']]
stock2.set_index(['date'], inplace = True)
print("stock数据量：",len(stock2.index))
stock=pd.concat([stock1, stock2])
#stock = stock.sort_values(by='date')
#stock=stock[['date','open','close','high','low','volume','code']]
stock.set_index(['date'], inplace = True) 
print(stock)
stock_new = stock.drop_duplicates(subset = 'date', keep = 'last')
#stock_new = stock.drop_duplicates()
stock_new=stock_new.sort_index(ascending =True)
print("合并后的数据量：",len(stock_new.index))
stock_new.to_csv('D:\\510050.csv')
