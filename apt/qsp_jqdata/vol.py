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