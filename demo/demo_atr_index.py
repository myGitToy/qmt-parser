#测试对于指数中所有个股计算ATR数值，最后输出每日的综合全部个股的ATR数据
import tushare as ts
import apt.vendor.tspro as tspro
from apt.vendor.tspro.tspro import tspro as ppp
from apt.os.data_load import  Data_Load as dl


def get_atr_index(market = ['主板' , '中小板' , '创业板' , '科创板']):
    a = ppp()
    code_list = a.get_code_list(market = market)
    for code in code_list:
        d = dl()
        df = d.load_data(code = code , start = '2019-01-01' , end = '2020-10-09' , ktype = 'D')


