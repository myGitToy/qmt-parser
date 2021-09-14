from apt.qsp_jqdata.vol import vol as vol
import pandas as pd
import tushare as ts
import datetime

a = vol()
#信息初始化
a.code = '002352.XSHE'
a.start = '2021/5/1'
a.end = '2021/9/14'
a.ktype = '1d'
a.myauth = False

#vol条件筛选
#vol_amt = a.money_between(LOW=0 ,HIGH =1982110598)
#print(vol_amt)

#vol异常值筛选
vol_abnormal = a.money_abnormal_change(criteria = 2 ,count = 5)
print(vol_abnormal)
