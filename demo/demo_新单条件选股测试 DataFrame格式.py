"""
本模块用于测试新的DataFrame形式返回的结果，暂时使用单条件筛选
"""
from apt.qsp_jqdata.vol import vol as VOL
from apt.qsp_jqdata.A import A as A
from apt.qsp_jqdata.base import base as base
from apt.vendor.jqdata.jqdata import data as data
from datetime import datetime
import pandas as pd
import tushare as ts
import talib as ta
pd.set_option('display.max_rows', None)
demo = VOL()
demo.start = datetime(2022,1,1)
demo.end = datetime.now()
demo.myauth = False
if __name__=="__main__":
    p = data(myauth = False)    
    code_list = p.get_all_code( type = "'stock'" , end_date = datetime.now() ,min_cap = 100 , max_cap = 10000)['code'].tolist()
    print(f"开始进行分析，选中的证券数量为{len(code_list)}")
    #成交量异常模型
    df_main = pd.DataFrame()
    for code in code_list[0:10000]:
        print(f"正在分析{code}；目前结果条目数为{df_main.shape[0]}")
        demo.code = code
        #成交量异常模型
        df = demo.money_abnormal_change(vol_ma = 20 , criteria = 2.5, N_day = 8 , count = 3 , interval = 10)[0]
        #均线多头排列模型
        #df = demo.A01B02_MA均线多头排列()[0]
        if df.empty == False:
            df_main = pd.concat([df_main, df.loc[df.result == 1]] , sort = False)

        #print(df_main)
        #df_main = pd.concat([df_main, df],sort = False)
    print(df_main.loc[df_main['date'] >= pd.to_datetime('2022/5/20')])