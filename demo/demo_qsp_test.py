import pandas as pd
from apt.qsp.k import k as k
from analyse import ATR as ATR

if __name__=="__main__":
    a = k(code = '688080' , start = '2020-01-02' , end = '2020-09-17' , ktype = 60 )
    print(a.ma_positive())