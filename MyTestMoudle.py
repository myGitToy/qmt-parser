# -*- coding: utf-8 -*-
'''
【测试模块1】
說明	
本测试模块需要完成的目标有：
1. 完成交割单的标准化读取和字段分类（如000651的问题）
2. 完成每日交易数据的标准化读取、字段类别、索引设定
3. 完成combine函数的测试

'''
from datetime import datetime,timedelta
import numpy as np
import pandas as pd
import tushare as ts
import logging
import os
import analyse
from analyse import ATR

def get_transactions_info(self , trade_log = None , column_include = None , column_not_include = None ,start =  None):
    """
    数据来源MySTP 仅为测试数据
    获取股票交割单信息
    从Myfunds中继承，目前不能选择交割单文件，读取指定目录和文件
    筛选买入和卖出信息，其余不要
    trade_log 需要读取的目录 默认为2018_fund.csv
    【未实装】column_include 需要读取的操作类型（数组格式）['证券买入','证券卖出'] 比如只输出证券交易类数据
    【未实装】column_not_include 不需要读取的操作类型（数组格式） ['融券购回"','融券回购'] 过滤掉国债逆回购类信息
    """
    #读取交割单信息
    if trade_log == None:
        trade_log='.\\trade\\2018_fund.csv'
        
    #df=pd.read_csv(trade_log,dtype={'证券代码': np.str,'交收日期':np.str,'成交数量':np.int,'发生金额':np.float},encoding='gb18030')
    df=pd.read_csv(trade_log,dtype={'证券代码': np.str,'交收日期':np.str,'成交数量':np.int,'发生金额':np.float})
    #交易日期时间序列化
    df['交收日期'] = pd.to_datetime( df['交收日期'] , format = '%Y%m%d' ) 
    #过滤融券购回和融券回购
    df=df[ ( df['操作'] != "融券购回" ) & ( df['操作'] != "融券回购" ) ] 
    df=df[ ( df['操作'] == "证券买入" ) | ( df['操作'] == "证券卖出" ) ] 
    #日期转换为datetime64[ns] 否则会在merge操作中因为两列属性不同和无法完成合并操作
    #df['Name'] = df['Name'].astype(np.datetime64)
    df['交收日期'] = pd.to_datetime(df['交收日期'])
    #输出交割单信息
    if start == None:
        #返回未经日期筛选的数据
        return df
    else:
        #返回起始日期后的数据
        return df[( df['交收日期'] >= start )]