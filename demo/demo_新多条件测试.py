#多条件测试
from apt.qsp_jqdata.A import A as A
from apt.qsp_jqdata.base import base as base
from apt.vendor.jqdata.jqdata import data as data
from datetime import datetime
import pandas as pd
import tushare as ts
import talib as ta

a = A()
a.start = datetime(2021,1,1)
a.end = datetime(2021,11,23)
a.myauth = False
if __name__=="__main__":
    #code_list= ['510300','510500','510050','510180','510900','159920','518880','159928','515030','512580','512170','512290','515220','515210','512720','515880','159995','159939','512760','512800','512880','512660','511010','511260','159949','512200','600089','600036','600519','600570','600958','300033','512200','300059','300236','603976','000651','601318','000063','159996','000001']
    #code_list = ['512830']
    #code_list = load_today_all()   
    #code_list = data.read_excel(file_name = '.\\data\\海龟模型\\自选股列表.xlsx' , sheet_name = '33指数')['证券代码'].tolist()
    p = data()
    code_list = p.get_all_code( type = "'stock'" , end_date = datetime(2021,11,19))['code'].tolist()
    #新高突破
    lst=[]
    for code in code_list:
        a.code = code
        if (a.A04B02_EMA均线多头排列() and \
                a.A04B06_EMA均线_线性回归角度(ma = 20 , adjust_N = 20 , count = 18 , low_value=-0.003 , upper_value= 0.003)) == True:  
           print(f"{code}均线平台整理且多头排列" )
           lst.append(code)
    print(lst)
    print(len(lst))