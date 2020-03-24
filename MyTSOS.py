# -*- coding: utf-8 -*-
'''
【tushare os系统】
所有涉及到文档读取 处理的代码归类到TSOS来处理，包括交割单、K线，历史分笔数据处理等等


'''
from datetime import datetime,timedelta
import numpy as np
import pandas as pd
import tushare as ts
import logging
import os

def get_ETF_list():
    #设置ETF路径
    file_path='.\\data\\ETF.csv'
        
    #df=pd.read_csv(trade_log,dtype={'证券代码': np.str,'交收日期':np.str,'成交数量':np.int,'发生金额':np.float},encoding='gb18030')
    df=pd.read_csv(file_path,dtype={'证券代码': np.str,'名称':np.str})
    print(df)
    #输出交割单信息

get_ETF_list()