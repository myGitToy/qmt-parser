import pandas as pd
import tushare as ts
from apt.qsp.k import k as k
from analyse import ATR as ATR
from apt.os.data_update import Data_Update as DL

if __name__=="__main__":
    d = DL()
    d.update_day(['000001'],last_day = '2020-09-25')
    print(ts.get_hist_data(code = '000001'))
    a = k(code = '159949' , start = '2020-01-02' , end = '2020-09-28' , ktype = "D" )
    print(a.k_new_high_count(80))
    df = ts.get_k_data(code = '510300' , ktype='60')
    #print(df)
