import pandas as pd
from apt.qsp_universal.base import base
from datetime import datetime
# 显示所有列
#pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
#测试ts复权因子
tspro = base()
tspro.code ='601318.sh'
tspro.vendor = tspro.vendor.tusharePro
tspro.start_date= datetime(1990,5,6)
tspro.end_date = datetime(2022,7,10)
tspro.fq = tspro.复权.动态复权
tspro.ktype = '1m'
#ts数据
df_ts = tspro.get_code_list()
#[['code','date','close','factor']]
print(df_ts)
#jqdata数据
tspro.code = '603986.XSHG'
tspro.vendor = tspro.vendor.jqdata
df_jqdata = tspro.get_k_data()
#print(df_jqdata)

    
