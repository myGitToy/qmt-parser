# -*- coding: utf-8 -*-
from datetime import datetime
from apt.qsp_universal.base import base as base
import numpy as np
import pandas as pd
import talib as ta
"""
【选股系统A】
目录树：
    A01 MA均线选股系统
    A02
    A03
    A04 EXPMA均线选股系统
"""
class NHNL(base):
    def get_NHNL(self , code_list = None , N_day = 250 , pct = 0.95):
        """
        NHNL系统
        输入：
            code_list:默认为空，即单代码模式；填入证券列表则进入多代码输出模式
            N_day 默认周期为250天 使用周线的则该参数为52周
            pct 默认新高的参数 0.95，意味着新高按照0.95执行；新低按照0.05掌握（新高新低均基于这个指标执行，需要上下对称）
        输出：DataFrame 返回 code|日期|收盘价|NH|NL
        """
        if code_list == None:
            #无证券代码列表，进入单代码模式
            return self.__get_data(N_day = N_day , pct = pct)
        else:
            #有列表，进入多代码模块
            df_main = pd.DataFrame()
            for code in code_list:
                self.code = code
                df = self.__get_data(N_day = N_day , pct = pct)
                df_main = pd.concat([df_main, df] , sort = False)
            return df_main

    def __get_data(self , N_day = 250 , pct = 0.95):
        '''
        内部代码，获取NHNL数据
        '''
        df = self.get_k_data()
        if df.empty == True:
            #无数据
            return pd.DataFrame()        
        df['NH_value'] = df['close'].rolling(N_day).quantile(pct , axis = 1)
        df['NL_value'] = df['close'].rolling(N_day).quantile(1 - pct , axis = 1)
        df['NH'] = np.where(df['close'] >= df['NH_value'] , 1 ,np.nan)
        df['NL'] = np.where(df['close'] <= df['NL_value'] , 1 ,np.nan)
        return df[['code','date','close','NH','NL']]



if __name__ == "__main__":
    # 列名与数据对其显示
    pd.set_option('display.unicode.ambiguous_as_wide', True)
    pd.set_option('display.unicode.east_asian_width', True)
    # 显示所有列
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    a = NHNL()
    a.code = '601012.XSHG'
    a.ktype = '1d'
    a.start_date = datetime(2010,1,1)
    a.end_date = datetime(2022,7,1)
    a.fq = a.复权.动态复权
    a.vendor = a.vendor.jqdata
    df = a.get_NHNL(code_list = ['601012.XSHG','601318.XSHG','600038.XSHG'])
    #df = a.get_NHNL(code_list = ['601012.sh','601318.sh','600038.sh'])
    d = datetime(2021,8,27)
    #按日汇总功能
    pivot = pd.pivot_table(df , index=['date'], values = ['NH','NL'] , aggfunc = np.sum)
    print(pivot)
    #print(df.query("code == '601012.XSHG'"))
    print(df.query("date == @d.date()"))
    pivot['diff'] = pivot['NH'] - pivot['NL']
    print(pivot)