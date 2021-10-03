from apt.qsp_jqdata.vol import vol as vol
from apt.qsp_jqdata.atr import ATR as atr
from apt.vendor.jqdata.jqdata import data
import pandas as pd
import tushare as ts
from datetime import datetime
from apt.vendor.jqdata.security import security as info
from apt.vendor.jqdata.finance.finance_valuation import finance_valuation as valuation
from apt.vendor.jqdata.money_flow import money_flow as money

a = vol(code =  '002352.XSHE' , start = datetime(2021,5,1) , end = datetime(2021,9,16) , ktype = '1d' , myauth = False)
t = atr(code =  '002709.XSHE' , start = datetime(2021,5,1) , end = datetime(2021,9,20) , ktype = '1d' , myauth = False)
inf = info(myauth = False)
print(1e2 / 100)
#信息初始化
#a.code = '002352.XSHE'
#a.start = '2021/5/1'
#a.end = '2021/9/14'
#a.ktype = '1d'
#a.myauth = False

#vol条件筛选
#vol_amt = a.money_between(LOW=0 ,HIGH =1982110598)
#print(vol_amt)
m = money(myauth = False)

m.get_money_flow(code = '688002.XSHG')
v = valuation(myauth = False)
print(v.get_code_type('510300.XSHG'))

#vol异常值筛选
vol_abnormal = a.money_abnormal_change(criteria = 2 ,count = 4 , N=4)
print(vol_abnormal)

dd = data(myauth = False)
dd.get_all_code(end_date =  datetime(2021,9,23) , local = True)

t.abnormal_atr()
inf.daily_update()

