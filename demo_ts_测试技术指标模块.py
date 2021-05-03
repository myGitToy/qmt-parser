# -*- coding: utf-8 -*-
"""
文档说明【历史分笔数据】：
    所有股票的历史分笔数据处理
    主要完成事件匹配和事件数据输出，为QAR分析提供csv格式的raw_data
    引用规范：请使用下列语句
        from tick import tick as tk
基本框架：

版本信息：
    version 0.1
    乔晖 2019/9/24
修改日志：

TODO LIST：
    
"""
import tushare as ts
import pandas as pd
import tushare.stock.indictor as ti
import fund
import apt
import datetime
from apt.os.data_load import Data_Load
from apt.os.data_update import Data_Update
from apt.vendor.jqdata.jqdata import data as data

class tick(object):
    def __init__(self,code,date):
        df = ts.get_tick_data(code,date,src='tt')
        print(df)
    pass

if __name__:
    code = "601318.XSHG"
    start = datetime.datetime(2021,1,1)
    end = datetime.datetime.now()
    ktype = '1d'
    data = data(myauth = False)

    df = data.get_k_data(code = code , start_date = start , end_date = end , ktype = ktype)
    print(df)
    df_ts =  ti.ema(df , n = 14 , val_name='close')  
    print(df_ts)    #返回的是NP.ARRAY数据格式
    t=tick('512760','2020-02-27')
    df_raw = ts.get_hist_data('512760')
    df=ti.boll(df_raw )
    df = ti.ema(df)
    print(df)
    print(fund.init_value)

    
    


