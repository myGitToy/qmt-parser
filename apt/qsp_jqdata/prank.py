# -*- coding: utf-8 -*-
from datetime import datetime
from apt.qsp_jqdata.base import base
import numpy as np
import pandas as pd

"""
【分位数选股系统】


"""
class prank(base):
    def get_prank(self  ):
        #获取数据
        df = self.get_k_data()
        print(df)