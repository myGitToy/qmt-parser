# -*- coding: utf-8 -*-
'''
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
'''
from datetime import datetime
import numpy as np
import pandas as pd
import tushare as ts
import logging
import os

#显示所有列
pd.set_option('display.max_columns', None)
#显示所有行
pd.set_option('display.max_rows', None)
#设置value的显示长度为100，默认为50
pd.set_option('max_colwidth',100)


class Technical_Analysis():
    """技术分析主类，下设各种技术分析指标，每个指标一个类"""
    #关于network_OK的说明：默认需要调用network_connection才能返回正确的结果，如果之前调用过，再使用network_OK可节约ping，增加效率
    network_OK=None
    #tushare社区的token
    _token = "55297f16c0119146589e059db315ba28a9412e89ec9f91e538e655b2"
    def network_connection(self,testing_url = None):
        """检查网络连接情况，可自定义网址，默认ping 百度；连通返回True 断开返回False"""
        print("CHECKING NETWORK CONNECTION......")
        url=testing_url
        try:
            if url is None:
                exit_code = os.system("ping www.baidu.com")
            else:
                exit_code = os.system("ping %s" % url)          
            #网络连通 exit_code == 0，否则返回非0值 抛出错误异常 被后续try except 捕获
            if exit_code:
                raise Exception('connect failed.') 
        except:
            self.network_OK = False
            return False
        else:
            self.network_OK = True
            return True

    def get_data(self):
        """获取基本数据用于技术分析，有网络：从get_his_data；无网络：从本地文档"""
        """如果网络断开，则读取本地文档用于技术分析"""
        if self.network_OK is None:
            print ("请检查语句，应先检查网络连接，XX.network_connection")
        elif True:
            #网络连接正常
            pro = ts.pro_api(self._token)
            df = ts.get_k_data(code = self.code,end = self.end,start = self.start)
            #print(df)
            return df
        elif False:
            #网络连接不正常
            df=pd.read_csv('.\\data\\day\\%s.csv' % (self.code))
            #print(df)
            print("网络连接不正常，读取本地文件")
            return df
        else:
            print("未知错误，请检查代码")

        #df=pd.read_csv('.\\data\\day\\%s.csv' % (self.code))
        #print(df)
        pass

    def __init__(self,code=None,start=None,end=None):
        """
        初始化
        输入：
            code 证券代码；
            start：开始日期
            end：结束日期
        返回：
        """
        self.code=code
        self.start=start
        self.end=end

class CDP(Technical_Analysis):
    """CDP类，继承自TA"""
    """
    def __init__(self,code=None,start=None,end=None):
        ####这里删除了初始化代码，直接使用父类，下面的代码使用super也是可行的
        #调用父类进行初始化
        super(CDP,self).__init__()
    """
    def cal_CDP(self,idx_tomorrow=False):
        """计算CDP"""
        #默认CDP计算使用的是前一天的数据，但如果idx_tomorrow=True，则输出预测第二个交易日的数据，且只输出一行
        if idx_tomorrow is False:
            #计算整个矩阵
            df = super(CDP,self).get_data()
            #CDP = (最高價 + 最低價 + 2*收盤價) /4
            df['CDP'] = (df['high'].shift(1)+df['low'].shift(1)+2*df['close'].shift(1)) / 4
            #最高值(AH)、(NH)、近低值(NL)及最低值(AL)
            #最高值AH = CDP + (最高價 - 最低價)
            df['AH']=df['CDP'] + (df['high'].shift(1) - df['low'].shift(1))
            #近高值NH = 2*CDP - 最低價
            df['NH']=2 * df['CDP'] - df['low'].shift(1)
            #近低值NL = 2*CDP - 最高價
            df['NL']=2 * df['CDP'] - df['high'].shift(1)
            #最低值AL = CDP - (最高價 - 最低價)
            df['AL']= df['CDP'] - (df['high'].shift(1)-df['low'].shift(1))
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
  
        #df2 = ts.get_today_ticks('510300')
        #print(df2.head(100))

                

if __name__=="__main__":
    a = CDP(start = '2019-10-01')
    #检查网络
    a.network_connection()
    print("连接状态：%s" % a.network_OK)
    #计算CDP
    cdp_list=['510300','512880','512580','512760']

    for i in cdp_list:
        x = CDP(code=i,start = "2019-10-01")
        x.network_OK=a.network_OK
        df=x.cal_CDP(idx_tomorrow=True)
        print(df)






"""
   获取个股CDP数据
    Parameters
    ------
      code:string
                  股票代码 e.g. 600848
      start:string
                  开始日期 format：YYYY-MM-DD 为空时取到API所提供的最早日期数据
      end:string
                  结束日期 format：YYYY-MM-DD 为空时取到最近一个交易日数据
      ktype：string
                  数据类型，D=日k线 W=周 M=月 5=5分钟 15=15分钟 30=30分钟 60=60分钟，默认为D
      retry_count : int, 默认 3
                 如遇网络等问题重复执行的次数 
      pause : int, 默认 0
                重复请求数据过程中暂停的秒数，防止请求间隔时间太短出现的问题
    return
    -------
      DataFrame
          属性:日期 ，开盘价， 最高价， 收盘价， 最低价， 成交量， 价格变动 ，涨跌幅，5日均价，10日均价，20日均价，5日均量，10日均量，20日均量，换手率
"""
