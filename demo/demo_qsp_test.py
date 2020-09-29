import pandas as pd
import tushare as ts
from apt.qsp.k import k as k
from analyse import ATR as ATR

if __name__=="__main__":
    a = k(code = '159949' , start = '2020-01-02' , end = '2020-09-28' , ktype = 60 )
    print(a.k_new_high_count(80))
    df = ts.get_k_data(code = '510300' , ktype='60')
    #print(df)
