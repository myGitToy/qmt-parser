#对于新高突破进行测试
#使用自定义证券列表，100小时线有3次以上的新突破
from apt.qsp.k import k as k
import pandas as pd

def condition1 ():
    return True

def condition2 ():
    return False

def condition3 ():
    return True


if __name__=="__main__":
    code_list= ['510300','510500','510050','510180','510900','159920','518880','159928','515030','512580','512170','512290','515220','515210','512720','515880','159995','159939','512760','512800','512880','512660','511010','511260','159949','512200','600089','600036','600519','600570','600958','300033','512200','300059','300236','603976','000651','601318','000063','159996','000001']
    start = '2020-05-01'
    end = '2020-09-11'
    ktype = '60'


    #print((not condition1()) | (not condition2()) |(not condition3()))

    #多条件TRUE FALSE测试1 :使用AND 条件  不会全部历遍
    if condition1() and condition2() and condition3():
        print(True)

    #多条件TRUE FALSE测试2 :使用多if语句 任何函数返回false 则跳出
    if condition1() :
        if condition2():
            if condition3():
                print(True)

    #多条件TRUE FALSE测试3 :使用all 所有条件均为True 才返回True 也会全部历遍
    if all([condition1(),condition2(),condition3()]):
        print(True)

    #均线向上
    for code in code_list:
        b = k()
        if (b.ma_positive(code =code , start = start , end = end ,  ktype = ktype ) == True) :
            print("%s均线向上" % (code))

    #新高突破
    for code in code_list:
        a = k()
        if (a.new_high_break(code =code , start = start , end = end ,  ktype = ktype , MA_HIGH_PERIOD = 100) == True) :
            print("%s新高突破" % (code))




            