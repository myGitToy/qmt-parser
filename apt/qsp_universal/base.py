# -*- coding: utf-8 -*-
from apt.vendor.jqdata.jqdata import data as jqdata
from apt.vendor.jqdata.base import base as jqbase
from apt.vendor.tspro.data import data as tsdata
from datetime import datetime , timedelta
from enum import Enum
import numpy as np
import pandas as pd

class base():
    """
    量化选股系统的基类(通用数据接口)
    使用jqdata.base作为基类
    """
    class vendor(Enum): 
        """
        选择数据供应商接口
        默认为tusharePro
        """
        tushare = 0 #tushare（未实装）
        tusharePro = 1 #tusharePro
        jqdata = 2 #jqdata
        akshare = 3   #akshare（未实装）
    class 复权(Enum):
        """
        选择复权类型
        默认为动态复权
        """
        不复权 = 0 #不进行复权处理
        前复权 = 1 #以最新日期基准，向前进行复权
        后复权 = 2 #以开始日期为基准，向后进行复权
        动态复权 = 3   #以结束日期为基准，向前进行复权
    def __init__(self , code = None , start_date = datetime(2021,1,1), end_date = datetime.now() , ktype = "1d" , fq = 复权.动态复权 , fwq = jqdata.数据源.localhost , myauth = False , vendor = vendor.tusharePro):
        """
        初始化
        输入：
            code 证券代码   e.g. 510300.XSHG
            start：开始日期  e.g. datetime
            end：结束日期    e.g. datetime
            ktype：K线类型 e.g. 1d 5m 30m 60m 
            fq：复权类型 默认动态复权
            fwq：服务器 默认为localhost
            myauth：是否向vendor进行登陆授权，默认是False；量化选股的设计初衷就是脱机本地读取数据
        返回：
        """
        self.code = code
        self.start_date = start_date
        self.end_date = end_date
        self.ktype = ktype
        self.fq = fq
        self.myauth = myauth
        self.server = fwq
        self.vendor = vendor
        #数据校验环节：
        #1. 证券代码不能为空
        #if code == None:
            #raise ValueError(f'证券代码不能为空')
        #2. 开始日期必须早于结束日期（两个日期start end 必须是同一类型）
        #start和end数据类型统一成datetime(对应bug id：244 未实装)
        #if (isinstance(start , str) == True and :
            #start = datetime.datetime(start)
        if start_date  > end_date:
            raise ValueError(f'开始日期必须早于结束日期')
        #3. K线类型校验
        if ktype not in ('1d','60m','30m','15m','5m','1m'):
            raise ValueError(f'不支持的K线类型：{ktype}')

    def get_k_data(self):
        """
        通用数据接口 获取指定日期间的K线数据
        由于tushare目前不含factor数据，因此本模块未完全可用
        输入：
            无
        返回：
            dataframe ：包含开盘 收盘 最高 最低 成交量 成交额 代码
        """
        if self.vendor == self.vendor.tusharePro:
            a = tsdata()
            a.myauth = self.myauth
            a.数据源 = self.server
            a.start_date = self.start_date
            a.end_date = self.end_date
            a.fq = self.fq
            a.code = self.code
            a.ktype = self.ktype
            df = a._data__get_k_data_ak()
            return df
        elif self.vendor == self.vendor.jqdata:
            a = jqdata(rds_host = self.server , myauth = self.myauth)
            #此处的get_k_data从vendor.jqdata.data.get_k_data取数据，非tushare
            df = a.get_k_data(code = self.code , start_date = self.start_date , end_date = self.end_date , ktype = self.ktype , fq = self.fq)
            return df
        elif self.vendor == self.vendor.akshare:
            print("展示不支持akshare数据获取")
            return pd.DataFrame()
        else:
            raise ValueError(f'不支持此数据供应商，请检查输入！')

    def get_code_list(self):
        """
        通用数据接口 获取证券代码列表
        输入：
            无
        返回：
            dataframe ：
        """
        if self.vendor == self.vendor.tusharePro:
            a = tsdata()
            a.myauth = self.myauth
            a.数据源 = self.server
            a.start_date = self.start_date
            a.end_date = self.end_date
            a.fq = self.fq
            a.code = self.code
            a.ktype = self.ktype
            #获取证券列表

        elif self.vendor == self.vendor.jqdata:
            a = jqdata(rds_host = self.server , myauth = self.myauth)
            #此处的get_k_data从vendor.jqdata.data.get_k_data取数据，非tushare
            #获取证券列表

        elif self.vendor == self.vendor.akshare:
            print("展示不支持akshare数据获取")
            return pd.DataFrame()
        else:
            raise ValueError(f'不支持此数据供应商，请检查输入！')

    def get_rolling_k_等待删除(self , ktype = "1d"):
        """
        【此处不确定是否需要删除】
        抽取出来的总类，用于获取最新的K线数据，含自动更新
        输入：
            ktype：K线类型 e.g. D 60 30
        返回：
            根据K线类型计算出来的当日K线总条数 
        """
        if ktype == "1d":
            #日线数据
            return 1
        elif ktype in ('15m','30m','60m'):
            #K线数据（文本类型）
            return 60 / int(ktype[0:2]) * 4
        elif ktype in ('5m'):
            return 48
        elif ktype in ('1m'):
            #K线数据（数字类型）
            return 240
        else:
            print("K线类型输入无效，按照默认日线数据返回结果")
            return 1