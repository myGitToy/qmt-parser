#多条件测试
from apt.qsp.k import k as k
from apt.qsp.vol import vol as vol
from apt.vendor.tspro.tspro import tspro as tspro
import pandas as pd
from apt.os.data_update import Data_Update as DL
def load_today_all():
    '''
    [加载当日实时数据]######
    函数说明 乔晖 2018/4/25
    从硬盘中获取当日交易的数据，数据由update_today_all提供更新
    【行情不含基金和ETF】
    读取目录在/data/today_all.csv
    '''
    allcode=[]
    #载入代码
    df=pd.read_csv('.\\data\\today_all.csv')
    #筛选代码
    df.set_index(['code'], inplace = True) 
    for i in df.index:
        #补0后的代码
        idx = "%06d" % i
        #当前价格
        
        try:
            trade=float(df.loc[i,['trade']])
        except :
            trade=0
        #print("%s交易价格为%s" % (idx,trade))
        if trade==0:
            #未交易，不写入代码列表
            #print('%s未交易%s' % (idx,trade))
            allcode.append(idx)
        else:
            allcode.append(idx)
    return allcode
if __name__=="__main__":
    #code_list= ['510300','510500','510050','510180','510900','159920','518880','159928','515030','512580','512170','512290','515220','515210','512720','515880','159995','159939','512760','512800','512880','512660','511010','511260','159949','512200','600089','600036','600519','600570','600958','300033','512200','300059','300236','603976','000651','601318','000063','159996','000001']
    #code_list = ['512830']
    #code_list = load_today_all()   
    dl = DL()
    code_list =dl.get_ETF_list()
    ts = tspro()
    #code_list = ts.get_code_list()
    #新高突破
    lst=[]
    for code in code_list:
        a = k(code = code , start = '2020-06-02' , end = '2021-03-29' , ktype = 60 , auto_update=False)
        b =  vol(code = code , start = '2020-06-02' , end = '2021-03-29' , ktype = 60 , auto_update=False )
        #if (a.new_high_break(code =code , start = start , end = end ,  ktype = ktype , MA_HIGH_PERIOD = 100 ,auto_update = False) == True) and (a.ma_positive(code =code , start = start , end = end ,  ktype = ktype , auto_update = False) == True):
        if a.ma_positive(POSITIVE_VALUE = -0.0005 ) and a.new_high_break( MA_HIGH_PERIOD = 100 , MINIMUM = 5 , MAXIMUM= 100 ) and b.amount_between(LOW = 1e7 , HIGH = 1e15):
           print("%s新高突破且均线向上" % (code))
           lst.append(code)
    print(lst)
    print(len(lst))