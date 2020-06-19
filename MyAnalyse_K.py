# -*- coding: utf-8 -*-
from datetime import datetime
import numpy as np
import pandas as pd
import tushare as ts
import logging
import os
from analyse import Technical_Analysis
from MyTSOS import Data_Load

class 均线系统(Technical_Analysis):
    def 均线向上(self , code = None, day = None , ktype = "D" , ma = 30 , filter_成交量 = 10000000 , filter_形态 = 0):
        """
        筛选K线形态 均线向上
        code_type: 代码类型 N = Normal 全部类型； ETF：沪深二级市场交易基金； 
        day: 交易日期
        ktype ：K线类型 默认为日线
        ma：XX均线向上 默认30均线
        filter_成交量：筛选最小入组的成交量，小于则不进行计算
        filter_形态阙值：均线向上需要 >0 ，对于某些均线走平的平台整理期，给与一定的宽容度
        start: 开始时间 可为空 默认全部读取
        end： 结束日期，可为空 默认为数据最后一天
        ktype： D/5/15/30/60 默认为日线
        """
        if code == None: 
            print('证券代码输入无效，请检查') 
            return None
        code = code.zfill(6)
        #K线类型处理
        if ktype == "D":
            #日线数据
            file_path=(".\\data\\day\\%s.csv" % (code))
        elif ktype in ('5','15','30','60'):
            #K线数据（文本类型）
            file_path=(".\\data\\%smin\\%s.csv" % (ktype,code))
        elif ktype in (5,15,30,60):
            #K线数据（数字类型）
            file_path=(".\\data\\%dmin\\%s.csv" % (ktype,code))
        else:
            print("K线类型输入无效，请检查")
            return None
        #读取数据
        df = Data_Load.load_data(code , start = day , ktype = ktype)
        print(df)
        
        pass

if __name__=="__main__":
    a= 均线系统()
    load = Data_Load()
    df = load.load_data( code= '510300' , start = '2020/4/21' , ktype = 'D')
    print(df)
    a.均线向上(code = '651' , day = '2020/4/21' ,ktype = 'D' , ma = 30)



