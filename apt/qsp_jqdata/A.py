# -*- coding: utf-8 -*-
from datetime import datetime
from apt.qsp_jqdata.base import base
from apt.vendor.jqdata.jqdata import data as data
import numpy as np
import pandas as pd
import talib as ta
"""
【选股系统A jqdata】
目录树：
    A01 MA均线选股系统
    A02
    A03
    A04 EXPMA均线选股系统
"""
class A(base):
    def A01B01_MA均线数据(self , ma_list = ['5','10','20','30','60','120']):
        """
        ]MA选股系统
        输入：
            证券代码，起止日期按照默认
            ma_list：需计算的均线 ['5','10','20','30','60','120']
        输出：DataFrame 各均线价格 列的规范：MA5|MA60|MA120
        """
        #df = self.get_k_data( code = self.code , start_date= self.start , end_date= self.end , ktype= self.ktype)
        df = self.get_k_data()
        if df.empty == True:
            #无数据
            return pd.DataFrame()        
        for ma in ma_list:
            df[f'MA{ma}'] = ta.MA(df['close'] ,  timeperiod = int(ma))
        return df

    def A01B02_MA均线多头排列(self , ma_list = ['10','20','60','120'] , N_day = 5 , count = 1):
        """
        MA均线多头排列
        输入：
            证券代码，起止日期按照默认
            ma_list：需计算的均线 ['10','30','60','120']
            N_day 几天内出现这种情况算是符合条件 默认为一周内，即5天。如需计算当天的情况，则N = 1
            count N周期内出现几次算符合条件 count <= N
            【备注】：正常情况下无需修改，默认5天内只有符合一次就算True；如果就是需要当天的均线排列结果，N_day=1 count=1
        输出：元组
            data[0]：DataFrame 包含日期 证券代码 结果
            data[1]：T/F值
        """
        #数据校验
        if count > N_day:
            raise ValueError(f'无法计算{N}天内出现{count}次的情况，请检查逻辑')
        #多导入的均线顺序进行排序
        ma_list.sort(key = int) #将K线列表以int整数的形式进行排列
        df = self.A01B01_MA均线数据(ma_list = ma_list)
        if df.empty == True:
            #数据为空，需要返回空值
            ##大代码量下进行滚动查询，不适合直接返回错误信息
            return pd.DataFrame() , False
            raise ValueError(f'数据为空，请检查！')
        #多头排列 Bull Market
        #判断ma均线的个数        
        ma_count = len(ma_list)
        #判断基准是两两比较，始终是前一个ma与后一个ma比较
        #如果均线多头排列 ['10','20','60','120']，则只需10>20;20>60;60>120则可以确认多头排列成立
        df['result'] = 1
        for n in range(0 , ma_count -1):
            df.loc[df[f'MA{ma_list[n]}'] > df[f'MA{ma_list[n+1]}'] , f'compare'] = 1
            df['result'] = df['result'] * df['compare']
            #重置df['compare']
            df['compare'] = np.nan
        #处理N_day内出现count次数
        df['result_sum'] = df['result'].rolling(N_day , min_periods = 1).sum()
        df['result'] = np.where(df['result_sum'] >= count , 1 , np.nan)
        #df.loc[df['result_sum'] < count , 'result'] = 0
        #设置最后一行参数，用于返回T/F值
        if df.iloc[-1].at['result'] == 1:
            last_row = True
        else:
            last_row = False
        #返回最后的结果 目前为元组类型，第一列为DataFrame 第二列为T/F值       
        return df[['code','date','result']] , last_row  
        """
        ##以下代码为历史陈旧记录，予以保留
        for n in range(0 , count - 1):
            short = df.iloc[-1].at[f'MA{ma_list[n]}']
            long = df.iloc[-1].at[f'MA{ma_list[n+1]}']
            if  short < long:
                return False
        return True
        """

    def A01B03_MA均线空头排列(self , ma_list = ['10','20','60','120'] , N_day = 5 , count = 1):
        """
        MA均线空头排列
        输入：
            证券代码，起止日期按照默认
            ma_list：需计算的均线 ['10','30','60','120']
            N_day 几天内出现这种情况算是符合条件 默认为一周内，即5天。如需计算当天的情况，则N = 1
            count N周期内出现几次算符合条件 count <= N
            【备注】：正常情况下无需修改，默认5天内只有符合一次就算True；如果就是需要当天的均线排列结果，N_day=1 count=1
        输出：元组
            data[0]：DataFrame 包含日期 证券代码 结果
            data[1]：T/F值
        """
        #数据校验
        if count > N_day:
            raise ValueError(f'无法计算{N}天内出现{count}次的情况，请检查逻辑')
        #多导入的均线顺序进行排序
        ma_list.sort(key = int) #将K线列表以int整数的形式进行排列
        df = self.A01B01_MA均线数据(ma_list = ma_list)
        if df.empty == True:
            #数据为空，需要返回空值
            ##大代码量下进行滚动查询，不适合直接返回错误信息
            return pd.DataFrame() , False
            raise ValueError(f'数据为空，请检查！')
        #空头排列 Bear Market
        #判断ma均线的个数        
        ma_count = len(ma_list)
        #判断基准是两两比较，始终是前一个ma与后一个ma比较
        #如果均线空头排列 ['10','20','60','120']，则只需10<20;20<60;60<120则可以确认空头排列成立
        df['result'] = 1
        for n in range(0 , ma_count -1):
            df.loc[df[f'MA{ma_list[n]}'] < df[f'MA{ma_list[n+1]}'] , f'compare'] = 1
            df['result'] = df['result'] * df['compare']
            #重置df['compare']
            df['compare'] = np.nan
        #处理N_day内出现count次数
        df['result_sum'] = df['result'].rolling(N_day , min_periods = 1).sum()
        df['result'] = np.where(df['result_sum'] >= count , 1 , np.nan)
        #df.loc[df['result_sum'] < count , 'result'] = 0
        #设置最后一行参数，用于返回T/F值
        if df.iloc[-1].at['result'] == 1:
            last_row = True
        else:
            last_row = False
        #返回最后的结果 目前为元组类型，第一列为DataFrame 第二列为T/F值       
        return df[['code','date','result']] , last_row  
        """
        ##以下代码为历史陈旧记录，予以保留
        for n in range(0 , count - 1):
            short = df.iloc[-1].at[f'MA{ma_list[n]}']
            long = df.iloc[-1].at[f'MA{ma_list[n+1]}']
            if  short > long:
                return False
        return True
        """

    def A04B01_EMA均线数据(self , ma_list = ['5','10','20','30','60','120']):
        """
        EXPMA选股系统
        输入：
            证券代码，起止日期按照默认
            ma_list：需计算的均线 ['5','10','20','30','60','120']
        输出：DataFrame 各均线价格 列的规范：EMA5|EMA60|EMA120
        """
        #df = self.get_k_data( code = self.code , start_date= self.start , end_date= self.end , ktype= self.ktype)
        df = self.get_k_data()
        if df.empty == True:
            #无数据
            return pd.DataFrame()
        for ma in ma_list:
            df[f'EMA{ma}'] = ta.EMA(df['close'] ,  timeperiod = int(ma))
        return df

    def A04B02_EMA均线多头排列(self , ma_list = ['10','20','60','120'] , N_day = 5 , count = 1):
        """
        EMA均线多头排列
        输入：
            证券代码，起止日期按照默认
            ma_list：需计算的均线 ['10','30','60','120']
            N_day 几天内出现这种情况算是符合条件 默认为一周内，即5天。如需计算当天的情况，则N = 1
            count N周期内出现几次算符合条件 count <= N
            【备注】：正常情况下无需修改，默认5天内只有符合一次就算True；如果就是需要当天的均线排列结果，N_day=1 count=1
        输出：元组
            data[0]：DataFrame 包含日期 证券代码 结果
            data[1]：T/F值
        """
        #数据校验
        if count > N_day:
            raise ValueError(f'无法计算{N}天内出现{count}次的情况，请检查逻辑')
        #多导入的均线顺序进行排序
        ma_list.sort(key = int) #将K线列表以int整数的形式进行排列
        df = self.A04B01_EMA均线数据(ma_list = ma_list)
        if df.empty == True:
            #数据为空，需要返回空值
            ##大代码量下进行滚动查询，不适合直接返回错误信息
            return pd.DataFrame() , False
            raise ValueError(f'数据为空，请检查！')
        #多头排列 Bull Market
        #判断ma均线的个数        
        ma_count = len(ma_list)
        #判断基准是两两比较，始终是前一个ma与后一个ma比较
        #如果均线多头排列 ['10','20','60','120']，则只需10>20;20>60;60>120则可以确认多头排列成立
        df['result'] = 1
        for n in range(0 , ma_count -1):
            df.loc[df[f'EMA{ma_list[n]}'] > df[f'EMA{ma_list[n+1]}'] , f'compare'] = 1
            df['result'] = df['result'] * df['compare']
            #重置df['compare']
            df['compare'] = np.nan
        #处理N_day内出现count次数
        df['result_sum'] = df['result'].rolling(N_day , min_periods = 1).sum()
        df['result'] = np.where(df['result_sum'] >= count , 1 , np.nan)
        #df.loc[df['result_sum'] < count , 'result'] = 0
        #设置最后一行参数，用于返回T/F值
        if df.iloc[-1].at['result'] == 1:
            last_row = True
        else:
            last_row = False
        #返回最后的结果 目前为元组类型，第一列为DataFrame 第二列为T/F值       
        return df[['code','date','result']] , last_row  
        
    def A04B03_EMA均线空头排列(self , ma_list = ['10','20','60','120'] , N_day = 5 , count = 1):
        """
        EMA均线空头排列
        输入：
            证券代码，起止日期按照默认
            ma_list：需计算的均线 ['10','30','60','120']
            N_day 几天内出现这种情况算是符合条件 默认为一周内，即5天。如需计算当天的情况，则N = 1
            count N周期内出现几次算符合条件 count <= N
            【备注】：正常情况下无需修改，默认5天内只有符合一次就算True；如果就是需要当天的均线排列结果，N_day=1 count=1
        输出：元组
            data[0]：DataFrame 包含日期 证券代码 结果
            data[1]：T/F值
        """
        #数据校验
        if count > N_day:
            raise ValueError(f'无法计算{N}天内出现{count}次的情况，请检查逻辑')
        #多导入的均线顺序进行排序
        ma_list.sort(key = int) #将K线列表以int整数的形式进行排列
        df = self.A04B01_EMA均线数据(ma_list = ma_list)
        if df.empty == True:
            #数据为空，需要返回空值
            ##大代码量下进行滚动查询，不适合直接返回错误信息
            return pd.DataFrame() , False
            raise ValueError(f'数据为空，请检查！')
        #空头排列 Bear Market
        #判断ma均线的个数        
        ma_count = len(ma_list)
        #判断基准是两两比较，始终是前一个ma与后一个ma比较
        #如果均线空头排列 ['10','20','60','120']，则只需10<20;20<60;60<120则可以确认空头排列成立
        df['result'] = 1
        for n in range(0 , ma_count -1):
            df.loc[df[f'EMA{ma_list[n]}'] < df[f'EMA{ma_list[n+1]}'] , f'compare'] = 1
            df['result'] = df['result'] * df['compare']
            #重置df['compare']
            df['compare'] = np.nan
        #处理N_day内出现count次数
        df['result_sum'] = df['result'].rolling(N_day , min_periods = 1).sum()
        df['result'] = np.where(df['result_sum'] >= count , 1 , np.nan)
        #df.loc[df['result_sum'] < count , 'result'] = 0
        #设置最后一行参数，用于返回T/F值
        if df.iloc[-1].at['result'] == 1:
            last_row = True
        else:
            last_row = False
        #返回最后的结果 目前为元组类型，第一列为DataFrame 第二列为T/F值       
        return df[['code','date','result']] , last_row 

    def A04B04_EMA均线_收盘价大于均线(self , ma= '10' , adjust_N = 1 , count = 1):
        """
        收盘价大于某条EMA均线
        输入：
            证券代码，起止日期按照默认
            ma：某条均线 默认为10日均线
            adjust_N : N天内符合条件就返回T 默认为当天
            count: N天内符合count次就返回True 默认为1
            例子：最后一个交易日收盘价大于EMA均线  adjust_ N = 1 ; count = 1
                    最后5个交易日出现2次大于EMA均线 adjust_ N = 5 ; count = 2
                    最后7个交易日每日收盘价均高于EMA均线 adjust_ N = 7 ; count = 7
        输出：T/F
        """
        lst = []
        lst.append(ma)
        df = self.A04B01_EMA均线数据(ma_list = lst)
        #丢弃NA数据，如果该列为NA，则返回是B 即收盘价小于EMA的NA数据
        df.dropna(how = 'any' , inplace = True)
        #如果数据量不足，返回False
        if df.empty == True:
            return False
        #A代表收盘价大于EMA均线，B代表收盘价小于EMA均线
        df['position'] = np.where(df['close'] >= df[f'EMA{ma}'] , 'A' , 'B')
        #下面这个方法也是可以的
        #df.loc[df['close'] >= df['EMA120'],['position2']] = 'A'
        #截取最后adjust_N的矩阵
        df = df[-adjust_N :]
        #print(df)
        #print(df['position'].isin(['A']))  返回是否包含A T/F
        #获取A出现的次数
        try:
            cc = df['position'].value_counts()['A']
        except:
            cc = 0
        #如果A次数大于目标值(count) 返回True
        if cc >= count:
            return True
        else:
            return False

    def A04B05_EMA均线_收盘价小于均线(self , ma= '10' , adjust_N = 1 , count = 1):
        """
        收盘价小于某条EMA均线
        输入：
            证券代码，起止日期按照默认
            ma：某条均线 默认为10日均线
            adjust_N : N天内符合条件就返回T 默认为当天
            count: N天内符合count次就返回True 默认为1
            例子：最后一个交易日收盘价小于EMA均线  adjust_ N = 1 ; count = 1
                    最后5个交易日出现2次小于EMA均线 adjust_ N = 5 ; count = 2
                    最后7个交易日每日收盘价均小于EMA均线 adjust_ N = 7 ; count = 7
        输出：T/F
        """
        lst = []
        lst.append(ma)
        df = self.A04B01_EMA均线数据(ma_list = lst)
        #丢弃NA数据，如果该列为NA，则返回是B 即收盘价小于EMA的NA数据
        df.dropna(how = 'any' , inplace = True)
        #如果数据量不足，返回False
        if df.empty == True:
            return False
        #A代表收盘价大于EMA均线，B代表收盘价小于EMA均线
        df['position'] = np.where(df['close'] >= df[f'EMA{ma}'] , 'A' , 'B')
        #下面这个方法也是可以的
        #df.loc[df['close'] >= df['EMA120'],['position2']] = 'A'
        #截取最后adjust_N的矩阵
        df = df[-adjust_N :]
        #print(df)
        #print(df['position'].isin(['A']))  返回是否包含A T/F
        #获取B出现的次数
        try:
            cc = df['position'].value_counts()['B']
        except:
            cc = 0
        #如果A次数大于目标值(count) 返回True
        if cc >= count:
            return True
        else:
            return False

    def A04B06_EMA均线_线性回归角度(self , ma= '20' , period = 2 , low_value = - 0.005 , upper_value = 0.005 , adjust_N = 1 , count = 1):
            """
            计算EMA均线的斜率角度
            备注：此方法对斜率角做了均一化处理。但不同周期下的数据略有不同，但是趋势是可以标准化的
            输入：
                证券代码，起止日期按照默认
                ma：某条均线 默认为10日均线
                period：talib必要参数，默认计算相邻两根 = 2
                low_value: 线性回归角度的下限值
                upper_value：线性回归角度的上限值 默认为-5至5的区间，定义为平台整理
                adjust_N : N天内符合条件就返回T 默认为当天 如果要计算平台整理，建议设置N = 20
                count: N天内符合count次就返回True 默认为1；如果要计算平台整理，建议设置count >=15
                例子：要计算最近20天内是否存在平台整理的情况  adjust_ N = 20 ; count = 15 ，value取值区间为（-5，5）
                        要计算最近20天内存在向上突破的情况  adjust_ N = 20 ; count = 8 ，value取值区间为（8，100）
            输出：T/F
            """
            lst = []
            lst.append(ma)
            df = self.A04B01_EMA均线数据(ma_list = lst)
            #如果数据为空，返回False
            if df.empty == True:
                return False
            #talib的斜率和角度计算公式因为归一化的原因，暂时无法使用，因此采用传统的计算方法
            #df['EMA_ANGLE'] = ta.LINEARREG_SLOPE(df[f'EMA{ma}'] , timeperiod = period)
            #使用当前值与前值的比率关系（传统的ma_positive处理方法）
            df['EMA_SLOPE'] = (df[f'EMA{ma}'] - df[f'EMA{ma}'].shift(1)) / df[f'EMA{ma}']
            #使用偏离度(检测下来也是不能用的)
            #df['EMA_CLOSE_RATE'] = (df['close'] - df[f'EMA{ma}'] ) / df[f'EMA{ma}']
            #df['EMA_ANGLE'] = ta.LINEARREG_SLOPE(df['EMA_CLOSE_RATE'] , timeperiod = period)
            #丢弃NA数据，如果该列为NA，则返回是B 即收盘价小于EMA的NA数据
            df.dropna(how = 'any' , inplace = True)
            #如果数据量不足，返回False
            if df.empty == True:
                return False
            #对均线斜率在low和upper区间的赋值1，不再区间的用0来填充NAN
            df.loc[(df['EMA_SLOPE'] >= low_value) & (df['EMA_SLOPE'] <= upper_value),'result'] = 1
            df.fillna({'result':0} , inplace = True)
            #df['result'] = np.where((df['EMA_ANGLE'] >= low_value) and (df['EMA_ANGLE'] <= upper_value) , 1 , 0)
            #对结果进行求和
            df['result_sum'] = df['result'].rolling(adjust_N).sum()
            #print(df.tail(20))
            #返回结果
            if df.iloc[-1].at['result_sum'] >= count :
                return True
            else:
                return False

    def A04B07_EMA均线_线性回归角度_传统计算方法(self , ma= '20' , period = 2 , low_value = - 0.005 , upper_value = 0.005 , adjust_N = 1 , count = 1):
        """
        计算EMA均线的斜率角度
        备注：对于EMA均线的话，其实使用收盘价与均线的偏离度也可以解释均线的斜率，并且和ATR数据结合，可以做到均一化处理
        输入：
            证券代码，起止日期按照默认
            ma：某条均线 默认为10日均线
            period：talib必要参数，默认计算相邻两根 = 2
            low_value: 线性回归角度的下限值
            upper_value：线性回归角度的上限值 默认为-5至5的区间，定义为平台整理
            adjust_N : N天内符合条件就返回T 默认为当天 如果要计算平台整理，建议设置N = 20
            count: N天内符合count次就返回True 默认为1；如果要计算平台整理，建议设置count >=15
            例子：要计算最近20天内是否存在平台整理的情况  adjust_ N = 20 ; count = 15 ，value取值区间为（-5，5）
                    要计算最近20天内存在向上突破的情况  adjust_ N = 20 ; count = 8 ，value取值区间为（8，100）
        输出：T/F
        """
        lst = []
        lst.append(ma)
        df = self.A04B01_EMA均线数据(ma_list = lst)
        #如果数据为空，返回False
        if df.empty == True:
            return False
        #talib的斜率和角度计算公式因为归一化的原因，暂时无法使用，因此采用传统的计算方法
        #df['EMA_ANGLE'] = ta.LINEARREG_SLOPE(df[f'EMA{ma}'] , timeperiod = period)
        #使用当前值与前值的比率关系（传统的ma_positive处理方法）
        df['EMA_SLOPE'] = (df[f'EMA{ma}'] - df[f'EMA{ma}'].shift(1)) / df[f'EMA{ma}']
        #使用偏离度(检测下来也是不能用的)
        #df['EMA_CLOSE_RATE'] = (df['close'] - df[f'EMA{ma}'] ) / df[f'EMA{ma}']
        #df['EMA_ANGLE'] = ta.LINEARREG_SLOPE(df['EMA_CLOSE_RATE'] , timeperiod = period)
        #丢弃NA数据，如果该列为NA，则返回是B 即收盘价小于EMA的NA数据
        df.dropna(how = 'any' , inplace = True)
        #如果数据量不足，返回False
        if df.empty == True:
            return False
        #对均线斜率在low和upper区间的赋值1，不再区间的用0来填充NAN
        df.loc[(df['EMA_SLOPE'] >= low_value) & (df['EMA_SLOPE'] <= upper_value),'result'] = 1
        df.fillna({'result':0} , inplace = True)
        #df['result'] = np.where((df['EMA_ANGLE'] >= low_value) and (df['EMA_ANGLE'] <= upper_value) , 1 , 0)
        #对结果进行求和
        df['result_sum'] = df['result'].rolling(adjust_N).sum()
        #print(df.tail(20))
        #返回结果
        if df.iloc[-1].at['result_sum'] >= count :
            return True
        else:
            return False


if __name__ == "__main__":
    dd = data(myauth = False)
    #dd.get_all_code(end_date =  datetime(2022,5,1) )
    pd.set_option('display.max_rows', None)
    demo = A(myauth = False)
    demo.code = '600313.XSHG'
    demo.start = datetime(2021,1,1)
    demo.end = datetime(2022,5,1)
    a = demo.A04B02_EMA均线多头排列(ma_list = ['10','20','60','120'])
    print(a[0])

