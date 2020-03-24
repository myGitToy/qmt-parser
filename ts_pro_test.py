import tushare as ts
ts.set_token('55297f16c0119146589e059db315ba28a9412e89ec9f91e538e655b2')
pro = ts.pro_api()

data = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
print(data)
print(ts.pro_bar(ts_code='600638.SH', adj='qfq', freq = 'D' , asset = 'E',start_date='2020-01-01'))
data.to_csv('.\\data\\tspro_stock_id.csv', encoding = 'utf_8_sig')
print(ts.get_hist_data('159949',start='2019-02-03', ktype='D'))   #只能获取股票数据，非ETF 获取的是交易日的盘后数据，盘中不会更新，含ma
print(ts.get_k_data('515350', start='2019-02-03',ktype='D'))   #可以获取ETF，盘中不会更新 缺点：只有VOL 没有amount