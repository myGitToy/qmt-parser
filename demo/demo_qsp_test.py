import pandas as pd
from apt.qsp.k import k as k
from analyse import ATR as ATR

if __name__=="__main__":
    a = k()
    df = a.k_new_high_count(code = '512880' , start = '2019-05-10' , end = '2020-09-09' ,  ktype='60' , MA_HIGH_PERIOD = 100)
    #print(df.getvalue('2020-09-07','close'))
    #df.to_csv('.\\data\\new_high\\test.csv')
    print(df)
    #atr = ATR()
    #atr.ge