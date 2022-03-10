# -*- coding: utf-8 -*-
from datetime import datetime
from apt.qsp_jqdata.base import base
from apt.vendor.jqdata.jqdata import data as data
import numpy as np
import pandas as pd
import talib as ta

class Momentum(base):
    """
    本模块为动量模型
    """
    def get_mtm(self , time = datetime.now() , ktype = '1d' , code_list = [] , N_list = [5,10,20] , to_csv = True):
    """
    获取动量模型的基础数据
    以沪深300为标的（可自选），列出N日内与指数的相对强弱关系
    输入：
        time：动量模型的基准时刻，可以是日期，也可以是带日期的时间点 默认是当前时间点
        kytpe：k线类型 默认是日线1d
        code_list：证券代码 需要计算的证券列表
        N_list：N日动量列表 默认是5 10 20 也可以接收自定义K线


            
    输出：
        单项指标于T日给出符合条件的波峰，假定第二日以开盘价格买入，测试Tn日的收益率，期间的最大有利波动，最大不利波动（即回撤）
    """
        #取出N日动量日中的最大日期数，全部DataFrame的合集即以此为基准
        #矩阵的模型
        """
        备注:每个code_list中都要取出max_N个数据，这里有几个问题:
        1. 如果用mysql直接查询，因为涉及到好几个代码，其实问题就转换成每个分类中取出前N个数据，mysql的解决方案比较复杂，
            且无法确定是否能走索引，因此不能确保查询速度；
            解决方案：每次查询单代码，查询后的结果用pandas进行拼接
        2. 每个代码的交易日不同，有些涉及到停牌的，可能按照某个统一的日期，或者统一的前N个数据，无法保证日期和数据相同，拼接上会有问题
            解决方案：前N日的列不按照日期进行，在初步的单代码数据列中先处理好，这样及时停牌，因为取的只是前N日数据，因此不影响；
                最终拼接时按照前N进行列的拼接，不涉及到日期的操作
        3. 刚上市的代码，可能前N日是没有数据的，因此在单代码数据返回时进行数据条目数的校验，不符合条件的直接剔除        
        """
        max_N  = max(N_list)
        max_df = None
        for code in code_list:
            
            a= self.get_k_data(code = code ,  end_date= time , ktype= ktype)
            print(a)
            sql = "select close from jqdata_{ktype} where code = '{code}' and "

    def get_mtm_rsi(self , code_list = [] , N = 100 , to_csv = True):
        """
        获取动量模型的相对强弱分析数据
        以沪深300为标的（可自选），列出N日内与指数的相对强弱关系
        输入：
            time：指标触发的时刻，可以是日期，也可以是待日期的时间点
            code：证券代码
            kytpe：K线类型

            
        输出：
            单项指标于T日给出符合条件的波峰，假定第二日以开盘价格买入，测试Tn日的收益率，期间的最大有利波动，最大不利波动（即回撤）
        """
        pass
