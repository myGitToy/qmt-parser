"""
本模块用于测试新的DataFrame形式返回的结果，暂时使用单条件筛选
"""
#from apt.qsp_jqdata.vol import vol as VOL
#from apt.qsp_jqdata import *
from apt.qsp_jqdata import vol,A
#from apt.qsp_jqdata.A import A as A
from apt.vendor.jqdata.jqdata import data as data
from datetime import datetime
import pandas as pd
import tushare as ts
import talib as ta
pd.set_option('display.max_rows', None)

demo = A.base()
vl = vol.vol()
k = A.A()
demo.code = '510300.XSHG'
demo.start = vl.start = k.start = datetime(2021,5,1)
demo.end = vl.end = k.end = datetime.now()
demo.myauth = vl.myauth = k.myauth = False


df2 = A.A.A01B01_MA均线数据(demo)   #竟然还可以这样引用

if __name__=="__main__":
    p = data(myauth = False)    
    code_list = p.get_all_code( type = "'stock'" , end_date = demo.end , min_cap = 0 , max_cap = 200)['code'].tolist()
    #成交量异常模型
    df_main = pd.DataFrame()
    for code in code_list[0:10000]:
        print(f"正在分析{code}；目前结果条目数为{df_main.shape[0]}")
        vl.code = k.code = code
        #成交量异常模型
        df_vol = vl.money_abnormal_change(vol_ma = 20 , criteria = 2.5, N_day = 8 , count = 3 , interval = 10)[0]
        #均线多头排列模型
        df_EMA = k.A04B02_EMA均线多头排列(ma_list=[5,20,60])[0]
        if df_vol.empty == False and df_EMA.empty == False:
            df_merge = pd.merge(df_vol , df_EMA , on = ['date','code'])
            df_merge['result'] = df_merge['result_x'] * df_merge['result_y']
            df_merge.dropna(subset = ['result'] , inplace = True)
        #print(df_merge)
        if df_merge.empty == False :
            df_main = pd.concat([df_main, df_merge.loc[df_merge.result == 1]] , sort = False)

        #print(df_main)
        #df_main = pd.concat([df_main, df],sort = False)
    print(df_main.loc[df_main['date'] >= pd.to_datetime('2022/4/1')])