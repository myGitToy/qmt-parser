# -*- coding: utf-8 -*-
import tushare as ts  
#df =ts.get_k_data(code='510300',ktype='D',index=False)
#rs=df.resample

df = ts.get_k_data('600618')
idx=df.index
print(idx)

#获取数据条目数
print('数据总数：',len(df))
#获取前3行
print('前三行数据为：')
print(df.head(3))
#获取后3行
print('前后行数据为：')
print(df.tail(3))
########获取某一天的数据  <---------非常重要
#进行数据index的转换，把时间变成指针
df_date = df.set_index('date', drop = True)
print('某一天的数据为为：')
print(df_date.loc['2018-04-20'])
print(df_date.loc['2018-04-20'].high)
print(df_date.index)
ind=df_date.index
for n in ind:
    print('交易日%s,收盘价%s' % (n,df_date.loc[n].close))


rows = df[0:3]
#获取第0,1行的开盘和最高数据
print(df.loc['0':'1',['open','high']])
#获取4/20和4/19的开盘和最高数据
print(df_date.loc['2018-04-19':'2018-04-20',['open','high']])

#print('数据总数：',df.ix[640].open)

#print(df.index)
#print(type(df))
#print(df.high)
#idx=df.index

#print(df.iloc[0,0])
#print(df)
#print(df[0][0])
#print(df.high)
#df.to_json('\000875.json',orient='records')
#或者直接使用
#print df.to_json(orient='records')
'''
df = ts.get_realtime_quotes('000581')
for row in df:
    print(df['code'])
print(df[['price']])
'''
#print(df.resample)
#m_date=df['date']
#print(m_date)
#print(df(date='2015-05-29'))
'''
#遍历keys
for key in df:
    print(key)
    
#遍历values
for value in df.items():
    # d.itervalues: an iterator over the values of d
    print(value)
#print(df['date'])
#print(len(df))


#print (dir(ts))

'''