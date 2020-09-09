# -*- coding: utf-8 -*-
from  apt.os.data_load import Data_Load as dl
from  apt.os.data_update import Data_Update as update
from datetime import datetime
"""
【K线选股系统】


"""
class k:
    def __init__(self):
        pass
    def __get_k_data(self , code : str , start = None , end = None , ktype = "60" , auto_update = True):
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

    def new_high_break(self , ):
        """
        突破前高
        输入：
            
        返回：
            True False

        """
    def k_new_high_count(self , code : str , start = None , end = None , ktype = "60" , MA_HIGH_PERIOD = 100 , auto_update = True):
        """
        【计算K线中指定周期新高的次数】
        常规使用小时线上100小时新高（ktype = 60 , MA_HIGH_PERIOD = 100）
        code start end ktype均为常规参数
        code start 必须输入
        end 选择输入
        【返回值】 dataframe 含最新数据的df
        MA_HIGH_PERIOD：计算新高的周期，需要和ktype配合使用
        【注意】数据前MA_HIGH_PERIOD中新高数据均为NA，因rolling前滚取不到数据的缘故
        """   
        #最后日期为空，则打开数据自动更新功能
        if  end == None:
            end = datetime.now().strftime("%Y-%m-%d")
            auto_update = True
        df = dl.load_data(self , code = code , start = start , end = end , ktype = ktype)
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

        #小时线100小时最高收盘价计算
        df['MAHR_100_HIGH'] = df['high'].rolling(MA_HIGH_PERIOD).max()
        #计算此时点的最高是否为新高
        df.loc[df.MAHR_100_HIGH == df.high,'new_high'] = 1    
        #累计回滚新高
        df = df.fillna(0)
        df['new_high_count'] = df['new_high'].rolling(MA_HIGH_PERIOD).sum()
        #数据错误风险提示
        if df.shape[0] <= MA_HIGH_PERIOD:
            print('数据输入可能存在错误，条目数小于rolling，请检查')
        #if df['MAHR_100_HIGH'] == df.copy()['high']:
        #    df['new_high_count'] = 1
        return df

