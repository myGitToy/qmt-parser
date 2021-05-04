# -*- coding: utf-8 -*-
from apt.vendor.jqdata.jqdata import data as jqdata
from apt.vendor.jqdata.base import base as basebase
import datetime
import numpy as np
import pandas as pd

class base():
    """
    量化选股系统的基类(聚宽数据接口)
    使用jqdata.base作为基类
    """
    def __init__(self , code = None , start = datetime.datetime(2021,1,1), end = datetime.datetime.now() , ktype = "1d" , fq = jqdata.复权.动态复权 , fwq = jqdata.数据源.localhost , myauth = True ):
        """
        初始化
        输入：
            code 证券代码   e.g. 510300.XSHG
            start：开始日期  e.g. datetime
            end：结束日期    e.g. datetime
            ktype：K线类型 e.g. 1d 5m 30m 60m 
            fq：复权类型 默认动态复权
            fwq：服务器 默认为localhost
            myauth：是否初始化jqdata授权（需要脱机读取时要设置为False）
            auto_update：数据自动更新 e.g. True False（暂未实装）
        返回：
        """
        self.code = code
        self.start = start
        self.end = end
        self.ktype = ktype
        #self.auto_update = auto_update
        self.fq = fq
        self.myauth = myauth
        self.server = fwq


    def get_k_data(self):
        """
        调用jqdata.data.get_k_data 用于获取最新的K线数据
        输入：
            无
        返回：
            dataframe ：包含开盘 收盘 最高 最低 成交量 成交额 代码
            注：只返回基础数据，其他类似于MA ATR信息由其他函数进行计算
        """
        a = jqdata(rds_host = self.server , myauth = self.myauth)
        #此处的get_k_data从vendor.jqdata.data.get_k_data取数据，非tushare
        df = a.get_k_data(code = self.code , start_date = self.start , end_date = self.end , ktype = self.ktype , fq = self.fq)
        return df
