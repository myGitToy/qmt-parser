# -*- coding: utf-8 -*-
from datetime import datetime
from apt.qsp_jqdata.base import base
import numpy as np
import pandas as pd

"""
【成交量选股系统】


"""
class vol(base):
    def money_between(self , LOW = 0 , HIGH = 1e6 , x_rolling = 1 , N = 1):
        """
        计算区间成交金额
        HIGH LOW 成交额 1e8 = 1亿 1e6 = 100万
        N 需要计算N天的平均值（因为成交量存在忽大忽小的情况）
            默认值是计算当天的，即N = 1
        小技巧：
            计算成交额小于N： LOW = 0 ; HIGH = N
            计算成交额大于N： LOW = N； HIGH = 1e12
        x_rolling ：比如60m就需要计算连续4天的值做汇总，否则数据是不准确的
        【例】money_between(LOW = 12e8 , HIGH= 1e12 , N = 3)
            计算某代码在3天内的平均成交量是否在12亿以上
        【返回值】 T/F
        """   
        #获取数据
        df = self.get_k_data()
        #返回rolling数
        x_rolling = int(self.get_rolling_k(self.ktype))
        #截断函数，减少工作量
        df = df.iloc[-(x_rolling * N + 20):]
        #计算
        df['rolling_money'] = df['money'].rolling(x_rolling * N ).sum() / N
        #print(df)
        if (df.iloc[-1].at['rolling_money'] >= LOW) and ( df.iloc[-1].at['rolling_money'] <= HIGH ) :
            return True
        else:
            return False

    def money_abnormal_change(self , vol_ma = 20 , criteria = 2 , N = 5 , count = 1 ):
        """
        计算区间是否存在成交量异动
        vol_ma 需要回滚ma根均线的成交量均值作为比较基准，默认是20天均值
        criteria 异动的标准 默认为均值ma的两倍
        N 几天内出现这种情况算是符合条件 默认为一周内，即5天。如需计算当天的情况，则N = 1
        count N周期内出现几次算符合条件 count <= N
        【例】money_abnormal_change(range = 20 ,criteria = 3 , N = 3 , count = 2 )
            计算某代码是否在3天内有2次超过平均成交量3倍以上的情况
        【返回值】 T/F
        暂存，已无用 DataFrame：证券代码 日期 成交量异动？？？？？暂定 目前不确定  也可能是T/F形式
        """   
        #数据校验
        if count > N:
            raise ValueError(f'无法计算{N}天内出现{count}次的情况，请检查逻辑')
        #获取数据
        df = self.get_k_data()
        if df.empty == True:
            raise ValueError(f'数据为空，请检查！')
        #返回rolling数
        x_rolling = int(self.get_rolling_k(self.ktype))
        #截断函数，减少工作量
        df = df.iloc[-(x_rolling * vol_ma + 20):]
        #计算
        df['rolling_money'] = df['money'].rolling(x_rolling * vol_ma ).sum() / vol_ma
        df['m_div_ma'] = df['money'] / df['rolling_money']
        df.loc[df['m_div_ma'] >= criteria , 'abnormal'] = 1
        df = df.fillna(0)
        df['abnormal_amout'] = df['abnormal'].rolling(count).sum()
        #print(df)        
        if df.iloc[-1].at['abnormal_amout'] >= count :
            return True
        else:
            return False