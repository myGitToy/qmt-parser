# -*- coding: utf-8 -*-
from  apt.os.data_load import Data_Load as dl
from  apt.os.data_update import Data_Update as update
from datetime import datetime
from apt.qsp_jqdata.base import base
import numpy as np
import pandas as pd
"""
【CDP逆勢操作系統】

說明	應用前一天的最高價、最低價、及收盤價的計算與分析，將當日的股價變動範圍為五個等級，再利用本日開盤價的高低位置，做為超短線進出的研判標準。
【計算公式】
先求出昨日行情的CDP值(亦稱均價)
CDP = (最高價 + 最低價 + 2*收盤價) /4
再分別計算昨天行情得最高值(AH)、近高值(NH)、近低值(NL)及最低值(AL)
AH = CDP + (最高價 - 最低價)
NH = 2*CDP - 最低價
NL = 2*CDP - 最高價
AL = CDP - (最高價 - 最低價
【使用方法】	
以最高值(AH)附近開盤應追價買進
盤中高於近高值(NH)時可以賣出
盤中低於近低值(NL)時可以買進
以最低值(AL)附近開盤應追價賣出
CDP為當天軋平的超短線操作法，務必當天沖銷(利用融資融卷)軋平。若當天盤中無法達到所設定理想的買賣價位時，亦應以當日的收盤價軋平。
"""
class CDP(base):
    #CDP只迁移 没有完成测试
    """
    def __init__(self,code=None,start=None,end=None):
        ####这里删除了初始化代码，直接使用父类，下面的代码使用super也是可行的
        #调用父类进行初始化
        super(CDP,self).__init__()
    """
    def cal_CDP(self , idx_tomorrow = False):
        """计算CDP"""
        #默认CDP计算使用的是前一天的数据，但如果idx_tomorrow=True，则输出预测第二个交易日的数据，且只输出一行
        if idx_tomorrow is False:
            #计算整个矩阵
            df = super(CDP,self).get_data()
            #CDP = (最高價 + 最低價 + 2*收盤價) /4
            df['CDP'] = (df['high'].shift(1) + df['low'].shift(1) + 2 * df['close'].shift(1)) / 4 
            #最高值(AH)、(NH)、近低值(NL)及最低值(AL)
            #最高值AH = CDP + (最高價 - 最低價)
            df['AH'] = round(df['CDP'] + (df['high'].shift(1) - df['low'].shift(1)) , 3)
            #近高值NH = 2*CDP - 最低價
            df['NH'] = round(2 * df['CDP'] - df['low'].shift(1) , 3)
            #近低值NL = 2*CDP - 最高價
            df['NL'] = round(2 * df['CDP'] - df['high'].shift(1) , 3)
            #最低值AL = CDP - (最高價 - 最低價)
            df['AL'] = round(df['CDP'] - (df['high'].shift(1) - df['low'].shift(1))  , 3)
            #输出             
            print(df)
        else:
            #只获取当天的
            #【注意：这里有交易日当天的bug】
            df = super(CDP,self).get_data().tail(1)
            #CDP = (最高價 + 最低價 + 2*收盤價) /4
            df['CDP'] = (df['high'] + df['low'] + 2 * df['close']) / 4
            #最高值(AH)、(NH)、近低值(NL)及最低值(AL)
            #最高值AH = CDP + (最高價 - 最低價)
            df['AH'] = df['CDP'] + (df['high'] - df['low'])
            df['AH_pct'] = round(((df['AH'] - df['close']) / df['close']) * 100 , 2)
            #近高值NH = 2*CDP - 最低價
            df['NH'] = 2 * df['CDP'] - df['low']
            df['NH_pct'] = round(((df['NH'] - df['close']) / df['close']) * 100 , 2)
            #近低值NL = 2*CDP - 最高價
            df['NL'] = 2 * df['CDP'] - df['high']
            df['NL_pct'] = round(((df['NL'] - df['close']) / df['close']) * 100 , 2)
            #最低值AL = CDP - (最高價 - 最低價)
            df['AL'] = df['CDP'] - (df['high'] - df['low'])
            df['AL_pct'] = round(((df['AL'] - df['close']) / df['close']) * 100 , 2)
            #计算CDP对应的涨跌幅

            print(df)
        pass

