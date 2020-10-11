#测试对于指数中所有个股计算ATR数值，最后输出每日的综合全部个股的ATR数据
import tushare as ts
import pandas as pd
import apt.vendor.tspro as tspro
from apt.vendor.tspro.tspro import tspro as ppp
from apt.os.data_load import  Data_Load as dl
from apt.qsp.atr import ATR as atr


def get_atr_index(market = ['主板' , '中小板' , '创业板' , '科创板'] , start = None , end = None , ktype = 'D'):
    a = ppp()
    code_list = a.get_code_list(market = market)
    #总表
    result = None
    for code in code_list:
        #获取单独的ATR数据
        myatr = atr(code = code , start = start , end = end , ktype = 'D')
        df = myatr.get_atr()
        #拼接总表
        result = pd.concat([result, df])
        #print (result)
    #result = result['MAHR_30_DEV','MAHR_100_HIGH_DEV']
    gp = result.groupby(['date']).median()
    print(gp)
    gp.to_csv('.\\trade\\ATR_INDEX.csv', encoding = 'utf_8_sig')

h = get_atr_index(start = '2019-01-01' , end = '2020-10-09' , ktype = 'D')


