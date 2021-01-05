# -*- coding: utf-8 -*-
from  apt.os.data_load import Data_Load as dl
from  apt.os.data_update import Data_Update as update
from datetime import datetime
from apt.qsp_jqdata.base import base
import numpy as np
import pandas as pd
"""
【K线选股系统】
"""
class k(base):
    def get_k_data_delete(self , code : str , start = None , end = None , ktype = "60" , auto_update = True):
        """
        抽取出来的总类，用于获取最新的K线数据，含自动更新
        输入：
            code 证券代码  e.g. 510300
            start：开始日期 e.g. yyyy-mm-dd
            end：结束日期   e.g. yyyy-mm-dd
            ktype： K线类型 e.g. D 60 30
            auto_update：是否将K线数据更新至最新 默认值：True （False则使用csv中的数据，不进行联网更新）
        返回：
            dataframe ：包含开盘 收盘 最高 最低 换手率（依据代码类型） 代码
            注：只返回基础数据，其他类似于MA ATR信息由其他函数进行计算
        """
        #最后日期为空，则打开数据自动更新功能
        if  end == None:
            end = datetime.now().strftime("%Y-%m-%d")
            auto_update = True
        df = dl.load_data(self , code = code , start = start , end = end , ktype = ktype)
        #可能存在的一种情况：指定时间段内无数据，返回空dataframe
        if df.empty ==True:
           return pd.DataFrame()
        #两个日期序列化 last_index 为索引转换成日期，last_end为字符串转换成日期再按照指定格式输出
        last_index = df.last_valid_index().strftime( '%Y-%m-%d')
        last_end = datetime.strptime(end, '%Y-%m-%d').strftime( '%Y-%m-%d')
        if (auto_update == True) & (last_index != last_end):
            #证券代码转换成列表格式
            lst=[]
            lst.append(code)
            if ktype =='D':
                #自动更新至最新数据（日线数据）
                ########################################################################################
                #日线数据更新存在一些问题，删除最新的日期后，无法完成自动更新(手动删除csv最后几行的情况下)
                #正常日线数据目前测试下来是可以更新的
                update.update_day(self , code_list = lst )
            else:
                #自动更新至最新数据（小时数据）
                update.update_min(self , code_list = lst , min = ktype)
            #读取最新数据
            df = dl.load_data(self , code = code , start = start , end = end , ktype = ktype)
        return df

    def new_high_break(self , MINIMUM = 3 ,MAXIMUM = 100 , MA_HIGH_PERIOD = 100 ) :
        """
        突破前高
        此函数设有过滤系统，必须突破新高次数降低到0以后重新回升才会计算在内；下降过程中的突破新高次数递减的情况会被过滤掉
        输入：
            MINIMUM：突破前高大于多少返回True 默认为3
            MAXMUM：突破前高需要限定在多少以内 一般不会用到，先预留着，目前做到逻辑里面了，默认为100
            MA_HIGH_PERIOD 突破N均线 默认为100
                注：通常日线采用20天突破 小时线采用100小时突破
            auto_update：是否将K线数据更新至最新 默认值：True （False则使用csv中的数据，不进行联网更新） 关闭该参数将提升20%左右的性能
        
        返回：
            True False
        存在的问题：
            1. 如果在震荡行情中，前期有一个突破的动作，但是突破失败，由于首次突破后趋势还是正的，因此及时在下降通道中，根据规则还会有很长时间处于前高求和>0 趋势为正的情况
            2. 建议通过均线向上的条件进行过滤
        """
        #获取新高数据
        df = self.k_new_high_count( MA_HIGH_PERIOD = MA_HIGH_PERIOD )
        if df.empty == True:
            print("请检查代码%s" % (self.code))
            return False
        #设置新高的趋势，所以新高次数逐渐增加，则设置1；逐渐减少设置-1；不变设置0
        df['new_high_tendency'] = df['new_high_count'] - df['new_high_count'].shift(1)
        #将新高趋势=0的调整为NA，再ffill NA，从而将1或者-1（既连续化上升或下降）
        df.loc[df.new_high_tendency == 0 , 'new_high_tendency'] = np.nan
        df.fillna(method='ffill' , inplace = True)
        #输出df信息，通常用于调试
        #print(df[['code','new_high','new_high_tendency' ,'new_high_count']])
        #print(df.loc[:,'new_high_count'])
        if (df.iloc[-1].at['new_high_count'] >= MINIMUM) and (df.iloc[-1].at['new_high_count'] <= MAXIMUM) and (df.iloc[-1].at['new_high_tendency'] ==1):
            #同时满足新高次数在上下限之间且非下降趋势（即回到0以后再上升的情况）
            return True
        else:
            return False
        print(df.iloc[-1].at['new_high_count'])
        return df[['code','new_high','new_high_tendency','new_high_count']]



    def k_new_high_count(self , MA_HIGH_PERIOD = 100 ):
        """
        【计算K线中指定周期新高的次数】
        常规使用小时线上100小时新高（ktype = 60 , MA_HIGH_PERIOD = 100）
        【返回值】 dataframe 含最新数据的df
        MA_HIGH_PERIOD：计算新高的周期，需要和ktype配合使用
        【注意】数据前MA_HIGH_PERIOD中新高数据均为NA，因rolling前滚取不到数据的缘故
        """   
        #获取K线数据
        df = self.get_k_data()
        if df.empty == True:
            print("请检查代码%s" % (self.code))
            #本函数因为提供的dataframe 因此不能返回False 只能返回空数据
            return pd.DataFrame()
        #小时线100小时最高收盘价计算
        df['MAHR_100_HIGH'] = df['high'].rolling(MA_HIGH_PERIOD).max()
        #计算此时点的最高是否为新高
        df.loc[df.MAHR_100_HIGH == df.high , 'new_high'] = 1    
        #累计回滚新高
        df = df.fillna(0)  
        df['new_high_count'] = df['new_high'].rolling(MA_HIGH_PERIOD).sum()
        #数据错误风险提示
        if df.shape[0] <= MA_HIGH_PERIOD:
            print('数据输入可能存在错误，条目数小于rolling，请检查')
        #if df['MAHR_100_HIGH'] == df.copy()['high']:
        #    df['new_high_count'] = 1
        return df

    def ma_positive(self , MA = 30 , ROLLING_PERIOD = 3 , POSITIVE_VALUE = -0.0005 ) :
        """
        计算K线均线的斜率
        输入：
            MA :MA日/小时 均线；通常计算30日/小时均线 默认为30
            ROLLING_PERIOD：均线斜率的计算依据，一般使用3个周期的平均值，以规避一根线带来的干扰 默认为3
            POSITIVE_VALUE：大于多少才认为斜率为正 一般取一个很小的负值，这样震荡走势中略微向下的情况也会被判断会正 默认值-0.0005      
        返回：
            True False
        """
        df = self.get_k_data()       
        if df.empty == True:
            print("请检查代码%s" % (self.code))
            return False
        #df = df.iloc[-(MA + 10):]  #测试中需要注释掉这条，否则只会输出最新的数据
        #计算MA日/小时均线价格
        df['ma'] = df['close'].rolling(MA).mean()
        df['ma_slope'] = (df['ma'] - df['ma'].shift(1)) / df['ma']
        df['ma3_slope'] = df['ma_slope'].rolling(ROLLING_PERIOD).mean()
        #print(df)
        df.to_csv('.\\data\\159949_ma30.csv', encoding = 'utf_8_sig')
        if df.iloc[-1].at['ma3_slope'] >= POSITIVE_VALUE:
            return True
        else:
            return False
