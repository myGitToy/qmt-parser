# -*- coding: utf-8 -*-
from datetime import datetime
from apt.qsp_jqdata.base import base as base    #jqdata分析类接口
from apt.vendor.jqdata.jqdata import data as jqdata #jqdata数据类接口
import pandas as pd
class momentum(jqdata):
    """
    【动量模型】
    """
    def get_mtm(self , time = datetime.now() , ktype = '1d' , code_list = [] , N_list = [5,10,20] , flag_forward = False , column = ['date','code','close']):
        """
        获取动量模型的基础数据
        以沪深300为标的（可自选），列出N日内与指数的相对强弱关系
        输入：
            time：动量模型的基准时刻，可以是日期，也可以是带日期的时间点 默认是当前时间点
            kytpe：k线类型 默认是日线1d
            code_list：证券代码 需要计算的证券列表
            N_list：N日动量列表 默认是5 10 20 也可以接收自定义K线  
            flag_forward：用于获取N日之后X条数据，类似于后复权数据 默认为False
                在这种模式下，start_date为基准日期，先后输出count条数据
                其余模式end_date均为基准日期
                详见https://huiqiao.visualstudio.com/MyFunds/_workitems/edit/296
            column: 默认输出收盘价，也可以是一组列表
        输出：
            单项指标于T日给出符合条件的波峰，假定第二日以开盘价格买入，测试Tn日的收益率，期间的最大有利波动，最大不利波动（即回撤）
            备注:每个code_list中都要取出max_N个数据，这里有几个问题:
            1. 如果用mysql直接查询，因为涉及到好几个代码，其实问题就转换成每个分类中取出前N个数据，mysql的解决方案比较复杂，
                且无法确定是否能走索引，因此不能确保查询速度；
                解决方案：每次查询单代码，查询后的结果用pandas进行拼接
            2. 每个代码的交易日不同，有些涉及到停牌的，可能按照某个统一的日期，或者统一的前N个数据，无法保证日期和数据相同，拼接上会有问题
                解决方案：前N日的列不按照日期进行，在初步的单代码数据列中先处理好，这样及时停牌，因为取的只是前N日数据，因此不影响；
                    最终拼接时按照前N进行列的拼接，不涉及到日期的操作
            3. 刚上市的代码，可能前N日是没有数据的，因此在单代码数据返回时进行数据条目数的校验，不符合条件的直接剔除        
        """
        #取出N日动量日中的最大日期数，全部DataFrame的合集即以此为基准
        #矩阵的模型
        max_N  = max(N_list)
        max_df = None
        df_main = pd.DataFrame()
        for code in code_list:
            if flag_forward == True:
                #向未来时间模式，非正常模式；N日向后采集X个数据
                a = self.get_k_data( code = code , ktype = ktype , start_date = time , count = max_N , flag_forward = flag_forward , col = column)
            else:
                #正常模式；N日向前采集X个数据
                a = self.get_k_data( code = code , ktype = ktype , end_date = time , count = max_N , flag_forward =  flag_forward , col = column)
            df_main = pd.concat([df_main,a])
        #输出最终拼接的结果
        print(df_main)
