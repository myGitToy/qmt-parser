import tushare as ts
ts.set_token('55297f16c0119146589e059db315ba28a9412e89ec9f91e538e655b2')
pro = ts.pro_api()

data = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
print(data)
data.to_csv('.\\data\\tspro_stock_id.csv', encoding = 'utf_8_sig')