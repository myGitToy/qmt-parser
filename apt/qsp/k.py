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
    def k_new_high_count(self , code : str , start = None , end = None , ktype = "60" , MA_HIGH_PERIOD = 100 , auto_update = True):
        """
        【计算K线中指定周期新高的次数】
        常规使用小时线上100小时新高（ktype = 60 , MA_HIGH_PERIOD = 100）
        code start end ktype均为常规参数
        MA_HIGH_PERIOD：计算新高的周期，需要和ktype配合使用
        【注意】数据前MA_HIGH_PERIOD中新高数据均为NA，因rolling前滚取不到数据的缘故
        【规则】start 格式不限，但end只允许使用YYYY/MM/DD 
        【规则】df输出格式为YYYY-MM-DD
        """
        #检查end字符串格式
        
        if "-"  in end:
            print('请使用YYYY/MM/DD格式，不允许使用YYYY-MM-DD')
            return False
        
        df = dl.load_data(self , code = code , start = start , end = end , ktype = ktype)
        #两个日期序列化 last_index 为索引转换成日期，last_end为字符串转换成日期再按照指定格式输出
        last_index = df.last_valid_index().strftime( '%Y/%m/%d')
        last_end = datetime.strptime(end, '%Y/%m/%d').strftime( '%Y/%m/%d')
        if (auto_update == True) & (last_index != last_end):
            #自动更新至最新数据（小时数据）
            lst=[]
            lst.append(code)
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
        #if df['MAHR_100_HIGH'] == df.copy()['high']:
        #    df['new_high_count'] = 1
        return df

