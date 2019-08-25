import tushare as ts
df = ts.get_k_data('sh',ktype='D',autype='qfq')
df.to_csv('.\\data\\day\\上证指数.csv')
print(df)