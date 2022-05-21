"""
本模块用于测试新的DataFrame形式返回的结果，暂时使用单条件筛选
"""
from apt.qsp_jqdata.vol import vol as VOL
from apt.qsp_jqdata.base import base as base
from apt.vendor.jqdata.jqdata import data as data
from datetime import datetime
import pandas as pd
import tushare as ts
import talib as ta
pd.set_option('display.max_rows', None)
demo = VOL()
demo.start = datetime(2022,4,1)
demo.end = datetime.now()
demo.myauth = False
if __name__=="__main__":
    p = data(myauth = False)
    
    code_list = p.get_all_code( type = "'stock'" , end_date = datetime(2022,5,20),local = True)['code'].tolist()
    #成交量异常模型
    df_main = pd.DataFrame()
    for code in code_list[0:10000]:
        print(f"正在分析{code}；目前结果条目数为{df_main.shape[0]}")
        demo.code = code
        df = demo.money_abnormal_change(vol_ma = 20 , criteria = 3, N_day = 8 , count = 3 , interval = 10)[0]
        if df.empty == False:
            df_main = pd.concat([df_main, df.loc[df.result == 1]] , sort = False)

        #print(df_main)
        #df_main = pd.concat([df_main, df],sort = False)
    print(df_main.loc[df_main['date'] >= pd.to_datetime('2022/5/10')])