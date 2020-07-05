# -*- coding: utf-8 -*-

"""
【tushare os系统】
所有涉及到文档读取 处理的代码归类到TSOS来处理，包括交割单、K线，历史分笔数据处理等等

get_ETF_list
    从CSV文件中读取EFT列表，该列表定期更新

"""
from datetime import datetime,timedelta
import numpy as np
import pandas as pd
import tushare as ts
import logging
import os
def print_tree_list():
    print('''
    根目录：
    apt
        -os #文档类主目录
            -TSOS

    
    
    ''')
