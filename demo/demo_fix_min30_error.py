from  apt.os.data_update import Data_Update as update
from  apt.os.data_load import Data_Load as load
import tushare as ts
code_list = ['164808']
dl = update()
load = load()
#获取数据
pro = ts.pro_api()
data = pro.query('stock_basic', exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
print(data)
df = load.load_data(code = '000029' , ktype = "5")
#df = ts.get_k_data(code = '000029' , ktype = "5")
print(df)
dl.update_min(code_list , min = 30)
