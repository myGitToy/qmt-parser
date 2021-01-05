# -*- coding: utf-8 -*-
from  apt.os.data_load import Data_Load as dl
from  apt.os.data_update import Data_Update as update
from datetime import datetime
from apt.vendor.jqdata.jqdata import data as jqdata
import datetime
import numpy as np
import pandas as pd

class base():
    """
    量化选股系统的基类(聚宽数据接口)
    """
    def __init__(self , code = None , start =datetime.datetime(2021,1,1), end =datetime.datetime.now() , ktype = "1d" , fq = jqdata.复权.动态复权 , auto_update = True):
        """
        初始化
        输入：
            code 证券代码   e.g. 510300.XSHG
            start：开始日期  e.g. datetime
            end：结束日期    e.g. datetime
            ktype：K线类型 e.g. 1d 5m 30m 60m 
            fq：复权类型 默认前复权
            auto_update：数据自动更新 e.g. True False
        返回：
        """
        self.code = code
        self.start = start
        self.end = end
        self.ktype = ktype
        self.auto_update = auto_update
        self.fq = fq

    def get_rolling_k(self , ktype = "D"):
        """
        抽取出来的总类，用于获取最新的K线数据，含自动更新
        输入：
            ktype：K线类型 e.g. D 60 30
        返回：
            根据K线类型计算出来的当日K线总条数 
        """
        if ktype == "D":
            #日线数据
            return 1
        elif ktype in ('5','15','30','60'):
            #K线数据（文本类型）
            return 60 / int(ktype) * 4
        elif ktype in (5,15,30,60):
            #K线数据（数字类型）
            return 60 / ktype * 4
        else:
            print("K线类型输入无效，按照默认日线数据返回结果")
            return 1

    def get_k_data(self):
        """
        抽取出来的总类，用于获取最新的K线数据，含自动更新
        输入：
            auto_update：调用基类的值 是否将K线数据更新至最新 默认值：True （False则使用csv中的数据，不进行联网更新）
        返回：
            dataframe ：包含开盘 收盘 最高 最低 换手率（依据代码类型） 代码
            注：只返回基础数据，其他类似于MA ATR信息由其他函数进行计算
        """
        #最后日期为空，则打开数据自动更新功能
        return jqdata.get_k_data(code = self.code , start_date = self.start , end_date = self.end , ktype = self.ktype , fq = self.fq)
        if  self.end == None:
            self.end = datetime.now().strftime("%Y-%m-%d")
            self.auto_update = True
        df = dl.load_data(self , code = self.code , start = self.start , end = self.end , ktype = self.ktype)
        #可能存在的一种情况：指定时间段内无数据，返回空dataframe
        if df.empty ==True:
           return pd.DataFrame()
        #两个日期序列化 last_index 为索引转换成日期，last_end为字符串转换成日期再按照指定格式输出
        last_index = df.last_valid_index().strftime( '%Y-%m-%d')
        last_end = datetime.strptime(self.end, '%Y-%m-%d').strftime( '%Y-%m-%d')
        if (self.auto_update == True) & (last_index != last_end):
            #证券代码转换成列表格式
            lst=[]
            lst.append(self.code)
            if self.ktype =='D':
                #自动更新至最新数据（日线数据）
                ########################################################################################
                #日线数据更新存在一些问题，删除最新的日期后，无法完成自动更新(手动删除csv最后几行的情况下)
                #正常日线数据目前测试下来是可以更新的
                update.update_day(self , code_list = lst )
            else:
                #自动更新至最新数据（小时数据）
                update.update_min(self , code_list = lst , min = self.ktype)
            #读取最新数据
            df = dl.load_data(self , code = self.code , start = self.start , end = self.end , ktype = self.ktype)
        return df