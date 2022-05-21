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

    def money_abnormal_change(self , vol_ma = 20 , criteria = 2 , N_day = 5 , count = 1 , interval = 1 ):
        """
        计算区间是否存在成交量异动
        vol_ma 需要回滚ma根均线的成交量均值作为比较基准，默认是20天均值
        criteria 异动的标准 默认为均值ma的两倍
        N 几天内出现这种情况算是符合条件 默认为一周内，即5天。如需计算当天的情况，则N = 1
        count N周期内出现几次算符合条件 count <= N
        interval 信号间隔周期，interval内出现的重复信号予以忽略
        【重要提示】
            成交量异常的判断和K线类型是挂钩的，日线以下级别由于当天开盘前30分钟成交量的影响，会干扰选股结果
            目前不对K线类型做限制，但是需要使用者清楚明白分时线可能带来的误差
        【例】money_abnormal_change(vol_ma = 20 ,criteria = 3 , N = 3 , count = 2 , interval = 15)
            计算某代码是否在3天内有2次超过平均成交量3倍以上的情况，15天内的重复信号仅计算第一次
            用文字表达就是A股票在某日，存在N_day内存在count次成交量大于vol_ma平均成交量criteria次的情况，信号间隔周期interval以上
        【返回值】 元组
            0列：DataFrame 包含日期 证券代码 结果
            1列：T/F 只包含最后交易日是否满足条件的判断
        """   
        #数据校验
        if count > N_day:
            raise ValueError(f'无法计算{N}天内出现{count}次的情况，请检查逻辑')
        #k线类型校验（推荐但不报错）
        if self.ktype != "1d":
            print("使用了不推荐的K线类型，返回结果不保证精确度")
        #获取数据
        df = self.get_k_data()
        if df.empty == True:
            #数据为空，需要返回空值
            ##大代码量下进行滚动查询，不适合直接返回错误信息
            return pd.DataFrame() , False
            raise ValueError(f'数据为空，请检查！')
        #返回rolling数
        x_rolling = int(self.get_rolling_k(self.ktype))
        #截断函数，减少工作量（取消截断，因为后续要改为DataFrame返回输出，因此需要计算全部数据行）
        #df = df.iloc[-(x_rolling * vol_ma + 20):]
        #计算
        df['rolling_money'] = df['money'].rolling(x_rolling * vol_ma ).sum() / vol_ma
        df['m_div_ma'] = df['money'] / df['rolling_money']
        #增加[abnormal]列
        #含义：满足成交量放大条件的交易日，设置abnormal = 1
        df.loc[df['m_div_ma'] >= criteria , 'abnormal'] = 1
        df = df.fillna(0)
        #增加['abnormal_amout']列
        #含义：连续N_day天内满足成交量放大的天数，最后会用这个天数和count进行比较
        df['abnormal_amout'] = df['abnormal'].rolling(N_day).sum()
        #增加[result-1]列
        #含义：作为最后结果的前置列，输出0/1值，含义是是否满足count的要求
        df.loc[df['abnormal_amout'] >= count , 'result-1'] = 1
        df = df.fillna(0)
        #增加[result]列
        #含义：最后的输出结果，对interval进行判断，如果X天内重复计算则去除第二个以后的结果
        df['result'] = df['result-1'].rolling(interval).sum() * df['result-1']
        df.loc[df['result'] > 1 , 'result'] = 0
        #校验结果，输出全部列（仅用于测试，正常情况下注释掉）
        #print(df)
        #返回DataFrame中最后一行是否符合条件，这个返回值属于传统的T/F值
        if df.iloc[-1].at['abnormal_amout'] >= count :#此处不涉及到interval判断，仅判断最后一天是否符合条件
            last_row = True
        else:
            last_row = False
        #返回最后的结果 目前为元组类型，第一列为DataFrame 第二列为T/F值       
        return df[['code','date','result']] , last_row    
