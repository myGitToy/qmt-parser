# -*- coding: utf-8 -*-
'''
【海龟派系統】
原版001 创建于2020/1/4
說明	
使用《海龟模型》和《通向财务自由之路》两书中所提到的思想，建立测试版本的交易模型

模型需要涵盖：
    【买点模型】：不重要，占10%的比例。目前拟采用60min_MA30向上；10 20 30 均线多头排列，出现3根红柱，于第三根收盘价买入
    【仓位管理】：单股票不超过6unit；
    【头寸管理】：基于100万总金额，单仓位不超过100w 0.25%风险；P=C/R=2500/ATR
    【止损位置】：买入价-2ATR
    【止盈位置】：价格小于60min_MA20，-2unit；价格小于60minMA30，-2unit；价格小于买入价-2ATR，清仓

协同方式：
    【数据处理】：python+pandas
    【数据存储】：mysql
    【程序界面】：VB.NET
    【其他】：多账号管理；多策略管理；数据模型历史回测功能
'''
from datetime import datetime,timedelta
import numpy as np
import pandas as pd
import tushare as ts
import logging
import os
import analyse
from analyse import ATR
#from MyFunds import get_transactions_info


class STP():
    def __init__(self,code_list=None,start=None,end=None,account_amount=None,account_risk=None):
        """
        初始化
        输入：
            code_list  e.g. ['510300','512880','512290','512760']
            start：开始日期 e.g. 2019-10-01
            end：结束日期   
            account_amount：总资金 e.g 100万
            account_risk:单仓位风险 总资金的百分比里 e.g 0.25 意味着0.25%的100万，也就是2500元单仓位单波动损失
        返回：
        """
        self.code_list = code_list
        self.start = start
        self.end = end
        self.account_amount = account_amount
        self.account_risk = account_risk
    
    def transactions_process(self,df_trans = None):
        """
        处理交割单买卖信息
        
        """
        df_trans = df_trans[['']]

    def get_remaining_unit (self , df = None , day = None):
        """
        获取每日剩余头寸表
        输入： df 交割单；day 日期 默认为最后一天（暂未开通）
        输出： 日期 证券代码 证券名称 最后买入价格 剩余数量 市值 头寸units
        
        """
        #如果df为空，则默认读取指定目录的数据
        if df == None:
            df =  self.get_transactions_info()
        else:
            df = df

        #交割单信息汇总
        df = df[(df['操作']!="证券买入") | (df['操作']!="证券卖出") ] 
        #temp = df[(df['操作']!="证券卖出") ]
        #temp['成交数量'] = temp['成交数量'] * -1
        #df.loc[temp,'成交数量']= temp['成交数量']
        #print(temp)
        #df.loc['成交数量'] = -df[(df['操作']!="证券卖出") ]['成交数量'] 

        print(df.loc[df['操作'] == "证券卖出",].groupby(['证券代码']).成交数量.sum())
        
        #买卖拆分
        df_buy =  df[(df['操作']!="证券买入") ].groupby(['证券代码']).sum()
        df_sell =  df[(df['操作']!="证券卖出") ].groupby(['证券代码']).sum()
        #主数组 新建列
        df_main = pd.DataFrame(columns=['证券代码','成交数量','成交金额','发生金额','手续费'])

        #print(df_buy)
        #print(df_sell)
        #print(df)
        #print(12)
        #df_buy = df[(df['操作']!="证券买入") ]
        
        #df[df['操作'] == '证券卖出']


    def get_daily_units(self , trade_log = None , code = None , start =  None ):
        """
        获取每日股票账户持股余额 包含ATR R风险值 均线 最高价 止损 止盈等信息 基本上包含需要的全部信息
        输入： 
            trade_log 交割单信息 不选择则默认读取指定目录，或者也可以接受dateframe格式的矩阵
            code 证券代码 只可以接受代码，不接受代码组 默认输出全部代码
            start 开始日期 筛选指定日期以后的数据 默认输出全部
        """
        #从get_transactions_info中提取交割单信息
        df_trans = self.get_transactions_info(trade_log = trade_log , start = start )
        #筛选证券代码
        if code != None:
            df_trans = df_trans[( df_trans['证券代码'] == code )]
        print(df_trans)
        #获取交割单的最早日期
        oldest_day = df_trans.head(1).iloc[ 0,  df_trans.columns.get_loc('交收日期') ]
        oldest_day = oldest_day - timedelta(days = 60)
        #更新交割单中交易股票的列表
        df_code_list = df_trans.copy()    
        code_list = df_code_list['证券代码'].values.tolist()
        #合并同类项
        code_list = list(set(code_list))
        #通过获取的交割单中的证券列表，批量获取ATR信息，生成ATR表格
        atr = ATR(start = start ,ktype="D" )
        atr.network_OK = True
        df_atr = atr.cal_daily_ATR_list(code_list = code_list , start = start , ktype = 'D',  to_csv = False )
        #print(df_atr)
        for code in code_list:
            #循环读取
            pass


        #测试pivot数据
        #df_trans.pivot()



    def get_transactions_info(self , trade_log = None , start =  None):
        """
        获取股票交割单信息
        从Myfunds中继承，目前不能选择交割单文件，读取指定目录和文件
        筛选买入和卖出信息，其余不要
        """
        #读取交割单信息
        if trade_log == None:
            trade_log='.\\trade\\2018_fund.csv'
        
        #df=pd.read_csv(trade_log,dtype={'证券代码': np.str,'交收日期':np.str,'成交数量':np.int,'发生金额':np.float},encoding='gb18030')
        df=pd.read_csv(trade_log,dtype={'证券代码': np.str,'交收日期':np.str,'成交数量':np.int,'发生金额':np.float})
        #交易日期时间序列化
        df['交收日期'] = pd.to_datetime( df['交收日期'] , format = '%Y%m%d' ) 
        #过滤融券购回和融券回购
        df=df[ ( df['操作'] != "融券购回" ) & ( df['操作'] != "融券回购" ) ] 
        df=df[ ( df['操作'] == "证券买入" ) | ( df['操作'] == "证券卖出" ) ] 
        #日期转换为datetime64[ns] 否则会在merge操作中因为两列属性不同和无法完成合并操作
        df['交收日期'] = pd.to_datetime(df['交收日期'])
        #输出交割单信息
        if start == None:
            #返回未经日期筛选的数据
            return df
        else:
            #返回起始日期后的数据
            return df[( df['交收日期'] >= start )]

          


    def daily_board(self):
        """
        每日信息看板汇总
        1. 显示每日列表中股票的头寸 daily_unit
        2. 显示账户剩余头寸的信息，包括止损位、追加位
        3. 显示账户历史交易信息 
        """
        #载入交割单
        df_trans = self.get_transactions_info(start = self.start)
        #获取交割单的最早日期
        oldest_day = df_trans.head(1).iloc[ 0,  df_trans.columns.get_loc('交收日期') ]
        oldest_day = oldest_day - timedelta(days = 60)
        #更新交割单中交易股票的列表
        df_code_list = df_trans.copy()    
        ###将列表与自选股中的列表进行合并，成为一张新的列表
        #获取交割单中的证券列表
        code_list_trans = df_code_list['证券代码'].values.tolist()
        #合并同类项
        code_list_trans = list(set(code_list_trans))
        #两个列表合并
        code_list_init = self.code_list
        code_list = code_list_init + code_list_trans
        #再次合并同类项
        code_list = list(set(code_list))
        ###载入新的ATR信息
        #df_atr = ATR.cal_daily_ATR_list(self,code_list=code_list,start=oldest_day.strftime('%Y-%m-%d'))
        df_atr = self.daily_unit(code_list = code_list , start = oldest_day.strftime('%Y-%m-%d'))
        #重命名列，否则后续无法进行merge操作，key列名不一样
        df_atr.rename(columns={'code' : '证券代码' , 'date' : '交收日期'} , inplace = True)
        #重置索引，否则会出现重复索引报错
        df_atr.reset_index(drop = True , inplace = True)
        df_trans.reset_index(drop = True , inplace = True)
        #重置所需列，删除部分无用列
        df_atr = df_atr[['交收日期' , '证券代码' , 'ATR' , '1 unit' , '1 unit金额']]
        df_trans = df_trans[['证券代码' , '证券名称' , '交收日期' , '操作' , '成交数量' , '成交均价' , '成交金额' , '手续费' , '发生金额' ]]
        #交割单部分信息重新计算 发生金额 = 成交金额 + 手续费 但是以账户视角进行操作的，需要进行正负符号转换
        df_trans['发生金额'] = - df_trans['发生金额']
        #交割单与ATR信息拼接
        df_board = pd.merge(df_trans , df_atr , on = ['证券代码' , '交收日期'], how = 'left')   
        #加入计算列
        #实际本次买入的unit数量 actual unit
        df_board['act_unit'] = df_board['成交金额'] / df_board['1 unit金额']
        df_sell = df_board[(df_board['操作'] == '证券卖出' ) ].copy()       
        df_buy = df_board[(df_board['操作'] == '证券买入' ) ].sort_values(by=['交收日期']).copy()
        
        #插入需要计算的空列
        df_board = pd.concat([df_board , pd.DataFrame(columns = ['卖出价格', '卖出数量' , '卖出发生金额' ,  '剩余头寸' , 'R' , 'R/unit'])] , sort = False ).fillna(0)
        df_board['剩余头寸'] = 1
        #临时 提取生物医药
        df_board = df_board[(df_board['证券名称'] == '生物医药' ) ]
        #print(df_board)
        #提取所有卖出操作，然后进行计算

        for index, row_sell in df_sell.iterrows():
            sell_index = index
            sell_证券代码 = row_sell['证券代码']
            sell_成交均价 = row_sell['成交均价']
            sell_成交数量 = row_sell['成交数量']
            sell_成交金额 = row_sell['成交金额']
            sell_手续费 = row_sell['手续费']
            sell_发生金额 = row_sell['发生金额']
            print(sell_成交均价)
            print(index  , sell_成交均价,sell_成交数量)
            #获取临时操作矩阵 提取买入操作且证券代码符合的dataframe
            df = df_board[(df_board['操作'] == '证券买入' )  & (df_board['证券代码'] == row_sell['证券代码']) & (df_board['剩余头寸'] == 1)].copy()
            remain_price = 0
            remain_count = 0
            remain_amout = 0
            for index_buy , row_buy in df.iterrows():
                   #该笔交易未清算，进行买入卖出计算
                   if row_sell['成交数量'] > row_buy['成交数量']:
                       #单笔卖出（10000）能覆盖此笔买入（5000），则这条买入记录全部平仓完毕
                       #该笔买入的卖出价格 = 对应卖出的价格 
                       df_board.loc[index_buy,['卖出价格']] = row_sell['成交均价']
                       #该笔买入的清仓数量 = 当初买入的全部数量
                       df_board.loc[index_buy,['卖出数量']] = row_buy['成交数量']
                       #该笔买入对应的发生金额
                       #剩余未卖掉的数量 = 该笔卖出的数量 - 当初买入的数量
                       remain_count = row_sell['成交数量'] - row_buy['成交数量']
                       #剩余未卖掉的成交金额 = 该笔卖出的金额
                       remain_price = row_sell['成交均价']
                       #剩余卖出发生金额（含佣金的分摊部分） = 当初买入数量 / 该笔卖出数量 * 该笔发生金额
                       df_board.loc[index_buy,['卖出发生金额']] = row_buy['成交数量'] / row_sell['成交数量'] * row_sell['发生金额']
                       remain_amout = row_sell['发生金额'] - df_board.loc[index_buy,['卖出发生金额']]
                       #卖出发生金额 = 卖出数量/成交数量 * 发生金额 
                       
                       df_board.loc[index_buy,['剩余头寸']] = 0
                       break
                   elif row_sell['成交数量'] == row_buy['成交数量']:
                       #数量相等
                       df_board.loc[index_buy,['卖出数量']] = row_buy['成交数量']
                       df_board.loc[index_buy,['卖出价格']] = row_sell['成交均价']
                       df_board.loc[index_buy,['卖出发生金额']] = row_sell['发生金额']
                       df_board.loc[index_buy,['剩余头寸']] = 0
                       df_board.loc[index_sell,['剩余头寸']] = 0
                       break
                       pass

                   else:
                       #剩余的情况，即有
                       if remain_count == 0:
                           #这笔交易为原生交易，卖出数量 < 买入数量 直接完成交易
                           df_board.loc[index_buy,['卖出数量']] = remain_count
                           df_board.loc[index_buy,['卖出价格']] = row_sell['成交均价']
                           df_board.loc[index_buy,['卖出发生金额']] = row_sell['发生金额']
                           df_board.loc[index_buy,['剩余头寸']] = 0
                           #清空卖出的头寸
                           df_board.loc[index_sell,['剩余头寸']] = 0

                   pass
        print(df_board)

                    #进行卖出的计算


    def daily_unit(self , code_list = None , start = None):
        """
        用于每日列表股票的头寸计算
        1. 进行ATP初始化，输入股票列表等参数
        2. df = stp.daily_unit()
        3. 打印dataframe

        【TODO】这里的计算过程可能会移植到
        """
        #计算头寸占比
        atr_daily = ATR.cal_daily_ATR_list(self , code_list = code_list , start = start , to_csv=True)
        atr_daily.network_OK = True
        #丢弃NA值
        #df_main=atr_daily.dropna()     #会有提示信息https://stackoverflow.com/questions/20625582/how-to-deal-with-settingwithcopywarning-in-pandas
        #--->这里只要有过筛选操作并赋值给新的dataframe就会出现这样的错误信息，一定要用copy命令
        df_main = atr_daily.dropna().copy()
        #调用ATR接口完成，进行进一步数据加工    
        #计算ATR占比=收盘价/ATR 用百分比输出
        df_main['ATR%'] = (df_main['ATR'] / df_main['close']).apply(lambda x: format(x, '.2%'))  
        #计算1unit P=C/R=总金额*风险值/ATR
        df_main['1 unit'] = (self.account_amount  * self.account_risk /100 / df_main['ATR'] / 100).astype(int) * 100
        #计算1unit金额=1unit * 收盘价
        df_main['1 unit金额'] = df_main['1 unit'] * df_main['close']
        #计算1unit止损金额=2ATR * 1unit
        df_main['1 unit止损金额'] = 2 * df_main['ATR'] * df_main['1 unit']
        #计算止损金额占比=止损金额 / 总仓位
        df_main['占比'] = (df_main['1 unit止损金额'] / self.account_amount ).apply(lambda x: format(x, '.2%'))  
        #计算总仓位头寸=总金额/ATR 取整
        df_main['总仓位头寸'] = (self.account_amount / df_main['1 unit金额']).apply(lambda x: format(x, '.0f')) 
        #格式调整
        ##格式调整完以后就从数字格式变成了文本格式，因此无法再进行计算
        ###由于上面进行了.astype(int) 操作，因此后面的格式调整已无意义，仅留作参考
        #df_main['1 unit']=df_main['1 unit'].apply(lambda x: format(x, ',.0f'))  
        #df_main['1 unit止损金额']=df_main['1 unit止损金额'].apply(lambda x: format(x, ',.0f')) 
        #df_main['1 unit金额']=df_main['1 unit金额'].apply(lambda x: format(x, ',.0f'))
        #比如 1unit=22000，这里因为进行了格式调整，数字变成了文本，因此*2变成了2200022000 
        #df_main['test']=df_main['1 unit金额'] * 2            
        return df_main
if __name__=="__main__":
    #本地运行
    #初始化设置 这里输入的证券列表属于自选股范畴，没有纳入交割单中的代码
    stp=STP(code_list=['510300','510500','159949','512760','512880','512290','512580','512980','600460','000651','601318','512720','159995','515050','600089','159920','510900','600036'],start='2019-10-01',account_amount=1250000,account_risk=0.25)
    df = stp.daily_unit(code_list =stp.code_list , start = stp.start)
    #测试 每日账户持股清单输出
    #stp.get_daily_units(code='512290',start='2020-01-21') #带筛选的
    stp.get_daily_units(start='2019-01-21') #不带筛选，输出全部

    
    #指定证券代码和日期筛选
    df2=df[(df['code']=='512760') & (df['date']=='2019-12-03')]
    #下面的代码和上面等同，效果一样
    df2 = df[(df.code == '512780') & (df.date >= '2019-12-20')] 
    #输出最后一天
    ## 注：这里输出的规则按照日期进行排序，按照列表code_list中包含的数据量进行截取。如果有股票当天未交易，则会输出前一天的某一个值，带来不确定性
    df_last = df.sort_values(by='date')
    
    #print(df_last)
    print('最后交易日为： %s'  % (df_last.tail(len(stp.code_list)))) 

    #读取交割单
    #df_trans = stp.daily_board()

    #每日头寸汇总 还在测试中 未完成最终代码编写工作
    stp.get_remaining_unit()