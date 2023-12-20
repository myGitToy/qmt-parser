# -*- coding: utf-8 -*-
from datetime import datetime,date,timedelta
from apt.vendor.tspro.base import base as base
from apt.vendor.tspro.base import stock as stock
from apt.vendor.tspro.data import data as data
import tushare as ts
import akshare as ak
import pandas as pd
import numpy as np
import pandas as pd

class pro_api(data):
    """
    akshare数据接口层，调用方法请参看task 449
    https://huiqiao.visualstudio.com/MyFunds/_sprints/taskboard/MyFunds%20Team/MyFunds/2023Q1?workitem=449
    """
    def __init__(self):
        #初始化 接入token
        self.pro = ts.pro_api("55297f16c0119146589e059db315ba28a9412e89ec9f91e538e655b2")


if __name__ == '__main__':
    a = pro_api()
    a.start_date = datetime(2023,3,1,8)
    a.end_date = datetime(2023,3,20,16)
    a.code = '159949.SZ'
    a.ktype = '1min'
    #df = a.stock_basic()
    df = a.suspend_k()
    pd.set_option('display.max_rows', None)  # Set display option to show all rows

    