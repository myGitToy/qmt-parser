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
class tick(object):
    def __init__(self,code,date):
        df = ts.get_tick_data(code,date,src='tt')
        print(df)
    pass

if __name__:
    t=tick('512760','2020-02-27')
    df_raw = ts.get_hist_data('512760')
    df=ti.boll(df_raw )
    print(df)
    print(fund.init_value)
    


