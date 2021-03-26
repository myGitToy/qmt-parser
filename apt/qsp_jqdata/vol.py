# -*- coding: utf-8 -*-
from datetime import datetime
from apt.qsp_jqdata.base import base
import numpy as np
import pandas as pd

"""
【成交量选股系统】


"""
class vol(base):
    def amount_between(self , LOW = 0 , HIGH = 1e6 , x_rolling = 1 ):
        """
        计算区间成交量
        HIGH LOW 成交额 1e8=1亿 1e6=100万
        小技巧：
            计算成交额小于N： LOW = 0 ; HIGH = N
            计算成交额大于N： LOW = N； HIGH = 1e12
        x_rolling 回溯K线数，默认回滚计算一天的K线 不同K线周期会采用不同的值，不建议自行调整
        【返回值】 T/F
        """   
        #获取数据
        df = self.get_k_data()
        #返回rolling数
        x_rolling = int(self.get_rolling_k(self.ktype))
        #截断函数，减少工作量
        df = df.iloc[-(x_rolling + 20):]
        #计算
        df['cal_amount'] = df['close'] * df['volume'] * 100
        df['rolling_amout'] = df['cal_amount'].rolling(x_rolling).sum()
        #print(df)
        if (df.iloc[-1].at['rolling_amout'] >= LOW) and ( df.iloc[-1].at['rolling_amout'] <= HIGH ) :
            return True
        else:
            return False