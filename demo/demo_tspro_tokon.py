import tushare as ts
import apt.vendor.tspro as tspro
from apt.vendor.tspro.tspro import tspro as ppp
a = ppp()
code = a.get_code_list(market = ['创业板'] , st_filter = True)
print(code)
#pro = ts.pro_api()
#df = pro.stock_basic(exchange='SZSE')
#print(df)


pro = ts.pro_api()  
a.get_code_list()
#ts.set_token(a._tokon)
#调用交易日全部股票数据
#df = pro.daily(trade_date='20200918 ')
#调用单一股票的交易数据
#df = ts.pro_bar(ts_code = '000001.SZ' , start_date = '20200101 09:00:00' , end_date = '20200918 15:00:00' ,freq = 'D' )

print(df)   