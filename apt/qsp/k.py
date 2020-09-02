# -*- coding: utf-8 -*-
from  apt.os.data_load import Data_Load as dl
"""
【K线选股系统】


"""
class k:
    def __init__(self):
        pass
    def k_new_high_count(self , code : str , start = None , end = None , ktype = "D"):
        load = dl.load_data(self , code = code , start = start , end = end , ktype = ktype)
        return load

