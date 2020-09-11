import pandas as pd
from apt.qsp.k import k as k
from analyse import ATR as ATR

if __name__=="__main__":
    a = k()
    df = a.new_high_break(code = '512760' , start = '2020-02-10' , end = '2020-06-24' ,  ktype='60' , MA_HIGH_PERIOD = 100)
    #print(df.getvalue('2020-09-07','close'))
    #df.to_csv('.\\data\\new_high\\test.csv')
    print(df)
    
    #atr = ATR()
    #atr.ge