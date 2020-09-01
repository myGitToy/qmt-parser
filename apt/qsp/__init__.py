# -*- coding: utf-8 -*-

"""
【tushare qsp系统】
Quantitative stock picking 量化选股系统
所有涉及到选股的内容，包括利用日线、小时线进行K线、VOL线选股，基本面选股等等



"""
from datetime import datetime,timedelta
import numpy as np
import pandas as pd
import tushare as ts
import logging
import apt.os
def print_tree_list():
    print('''
    根目录：
    apt
        -qsp #文档类主目录
            -

    
    
    ''')
