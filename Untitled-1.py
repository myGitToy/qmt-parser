# -*- coding: utf-8 -*-
import pandas as pd
import tushare as ts 
#获取第一个df
df1 = ts.get_k_data('510050', start='2014-02-21',end='2014-04-01',ktype='D',autype='qfq')
#重构索引
df1.set_index(['date'], inplace = True)   
#获取第二个df
df2 = ts.get_k_data('510050', start='2014-01-01',end='2014-04-01',ktype='D',autype='qfq')
#重构索引
df2.set_index(['date'], inplace = True) 
#两个dataframe合并
df_new=pd.concat([df1, df2])
#检查去重
df_new = df_new.drop_duplicates()  
#按照索引[日期]进行排序，升序
print(df_new.sort_index(ascending = True))
