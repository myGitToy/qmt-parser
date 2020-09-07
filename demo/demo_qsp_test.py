from apt.qsp.k import k
import pandas as pd

a = k()
df = a.k_new_high_count(code = '159949' , start = '2019-05-10' , end = '2020-09-07' ,  ktype='60' , MA_HIGH_PERIOD =50)
df.to_csv('.\\data\\new_high\\test.csv')
print(df)