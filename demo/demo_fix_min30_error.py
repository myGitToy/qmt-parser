from  apt.os.data_update import Data_Update as update
from  apt.os.data_load import Data_Load as load
code_list = ['164808']
dl = update()
load = load()
#获取数据
df = load.load_data(code = '164808' , ktype = "30")
print(df)
dl.update_min(code_list , min = 30)
