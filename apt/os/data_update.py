# -*- coding: utf-8 -*-
from datetime import datetime,timedelta
import numpy as np
import pandas as pd
import sqlalchemy
import tushare as ts
import logging
import os
import datetime
#载入基类
from apt.os.tsos import TSOS
class Data_Update(TSOS):
    """
    数据更新类，继承自TSOS
    调用时请添加引用：from apt.os.data_update import Data_Update
    数据更新目前接受的是codelist 对时间格式没有要求
    单独的数据更新时间格式必须是YYYY-mm-dd
    """
    def __init__(self):
        pass

    def update_day(self , code_list='' , filter_last = 0 , last_day = None):
        '''
        [更新日线数据]######
        code_list: 需要更新的证券代码列表
        filter_last：需要过滤的数据量，如果出现当天交易日进行过了更新，则当日的数据不准确，需要去除旧数据中最后几条数据，因此可以接受参数输入
        last_day：数据更新的最后日期，如果不设置，默认为当天
        函数说明 乔晖 2020/4/8
        修正一系列已知问题，基本无错误，移植至TSOS->Data_Update列中
        原函数仅涉及保存，不进行新老文件的合并操作，因此重构
        '''
        ####步骤一：读取现有数据
        #设置最后默认的最后交易日
        if last_day == None:
            last_day = datetime.date.today()
        for code in code_list:
            #数据补零
            code = code.zfill(6)
            try:
                df_old = pd.read_csv('.\\data\\day\\%s.csv' % (code))
                if df_old.empty == True:
                    success = False
                else:
                    success = True       
            except IOError:
                #没有找到文件
                #print('error')
                success = False
            else:
                #读取成功
                pass
            if success:
                #读取成功，进行合并操作
                #处理旧数据
                df_old.set_index(['date'], inplace = True , drop = True)  
                #删除重复项【重要提示：由于未知原因，使用drop_duplicates依旧会出现重复，所以此处采用对索引进行判断，如果索引相同，则表示有重复】
                if df_old.index.is_unique == False:
                    df_old = df_old[~df_old.index.duplicated( keep = 'first' )]
                    print('原始数据有重复项，去重')
                #数据补零
                df_old['code'] = df_old['code'].astype(str)
                df_old['code'] = df_old['code'].str.zfill(6)
                df_old = df_old[['open','close','high','low','volume','code']]
                #过滤旧数据中最后几条
                if filter_last != 0:                    
                    df_old = df_old[:-filter_last] #测试环节用，删除部分最新数据以调试新老df的合并情况
                #获取最后更新日期
                #old_day = df_old.head(1).index.tolist()
                old_day = df_old.iloc[-1:].index.tolist()
                #print(old_day[0])
                if len(old_day) !=0 and old_day[0] == last_day:
                    #如果两个日期相同 则跳过合并
                    print('日线：%s 数据已是最新，跳过读取' % (code))
                    pass
                else:
                    #数据不为最新，进行更新操作
               
                    #旧数据量
                    old_count = df_old.shape[0]
                    #获取新数据
                    df_new = ts.get_k_data(code, ktype = 'D')
                    #如果最新数据为空，则表明该代码已许久未交易，停盘很久了（有时候ts pro会出错，导致采集到了）
                    if df_new.empty == True:
                        print("%s最新数据为空，请检查" % code)
                    else:
                        df_new.set_index(['date'], inplace = True)  
                        df_new = df_new[['open','close','high','low','volume','code']]
                        ###两个dataframe合并【按照日期进行关键词校对 注：日期date为索引】
                        df = pd.concat([df_old, df_new] , sort = True)
                        #检查去重
                        #df.drop_duplicates(keep = 'last', inplace = True)
                        #删除重复项【重要提示：由于未知原因，使用drop_duplicates依旧会出现重复，所以此处采用对索引进行判断，如果索引相同，则表示有重复】
                        if df.index.is_unique == False:
                            df = df[~df.index.duplicated(keep='last')]     #这里还有一个效率的问题，理论上旧数据不做去重，合并后再去重，但为了明确获取新老数据量的差别，因此做两次去重，降低一些效率
                            #print('合并后有重复项，去重')
                        #按照索引[日期]进行排序，升序
                        df = df.sort_index(ascending = True)
                        df = df[['open','close','high','low','volume','code']]
                        #df = df[~df.index.duplicated(keep='first')]
                        #总数据量
                        all_count = df.shape[0]
                        print('日线：%s读取完毕，新增数据量：%s条' % (code,all_count-old_count))
                        if all_count-old_count != 0:
                            #保存数据
                            df.to_csv('.\\data\\day\\%s.csv' % (code))
            else:
                #读取失败，说明目录无文件，直接写入
                #获取新数据并保存
                df_current = ts.get_k_data('%s' % (code), ktype = 'D' )
                if df_current.empty == False:
                    df_current.set_index(['date'], inplace = True)  
                    df_current.to_csv('.\\data\\day\\%s.csv' % (code))
                    print('日线：新增代码%s，数据量：%s条' % (code,df_current.shape[0]))
                else:
                    print('日线：代码%s 无数据' % (code))

    def update_min(self , code_list = '' , min = 60 , filter_last = 0 , last_day = None):
        '''
        [更新XX分钟数据]######
        函数说明 乔晖 2020/4/9
        code_list: 需要更新的证券代码列表
        min：需要更新XX分钟，默认为60分钟
        filter_last：需要过滤的数据量，如果出现当天交易日进行过了更新，则当日的数据不准确，需要去除旧数据中最后几条数据，因此可以接受参数输入
        具体步骤如下：
        1.获取每日开盘的数据，取得当日交易的股票列表
        2.从[5min]的文件夹中读取已有数据
        3.从[get_k_data]中读取新数据，存入临时文件夹并作读取动作 【此步骤因为目前无法为从文件读取的df和直接获取数据的df做去重处理】
        4.两者合并去重并排序
        5.写入原有文件
        '''
        ####步骤一：读取现有数据
        #设置最后默认的最后交易日
        if last_day == None:
            last_day = datetime.date.today().strftime('%Y-%m-%d')
        for code in code_list:
            #数据补零
            code = code.zfill(6)
            try:
                df_old = pd.read_csv('.\\data\\%smin\\%s.csv' % (min,code))
                if df_old.empty == True:
                    success = False
                else:
                    success = True       
            except IOError:
                #没有找到文件
                #print('error')
                success = False
            else:
                #读取成功
                pass
            if success:
                #读取成功，进行合并操作
                #处理旧数据
                df_old.set_index(['date'], inplace = True , drop = True)  
                #删除重复项【重要提示：由于未知原因，使用drop_duplicates依旧会出现重复，所以此处采用对索引进行判断，如果索引相同，则表示有重复】
                if df_old.index.is_unique == False:
                    df_old = df_old[~df_old.index.duplicated( keep = 'first' )]
                    print('原始数据有重复项，去重')
                #数据补零
                df_old['code'] = df_old['code'].astype(str)
                df_old['code'] = df_old['code'].str.zfill(6)
                #对列名进行检查  有部分数据原文件不含'amount','turnoverratio' 直接使用会报错
                if 'amount' not in df_old.columns:
                    df_old['amount'] = None
                if 'turnoverratio' not in df_old.columns:
                    df_old['turnoverratio'] = None
                df_old = df_old[['open','close','high','low','volume','amount','turnoverratio','code']]
                #过滤旧数据中最后几条
                if filter_last != 0:                    
                    df_old = df_old[:-filter_last] #测试环节用，删除部分最新数据以调试新老df的合并情况
                #获取最后更新日期
                old_day = df_old.iloc[-1:].index.tolist()
                #old_day = df_old.last_valid_index()[0:10]
                #print(old_day[0].strftime('%Y-%m-%d'))
                if len(old_day) != 0 and old_day[0][0:10] == last_day:
                    #如果两个日期相同 则跳过合并
                    print('%s分钟线：%s 数据已是最新，跳过读取' % (min , code))
                    pass
                else:
                    #数据不为最新，进行更新操作                
                    
                    #旧数据量
                    old_count = df_old.shape[0]
                    #获取新数据
                    df_new = ts.get_k_data('%s' % (code) , ktype='%s' % (min))
                    #如果最新数据为空，则表明该代码已许久未交易，停盘很久了（有时候ts pro会出错，导致采集到了）
                    if df_new.empty == True:
                        print("%s最新数据为空，请检查" % code)
                    else:
                        df_new.set_index(['date'] , inplace = True)  
                        df_new = df_new[['open','close','high','low','volume','amount','turnoverratio','code']]
                        ###两个dataframe合并【按照日期进行关键词校对 注：日期date为索引】
                        df = pd.concat([df_old, df_new] , sort = True)
                        #检查去重
                        #df.drop_duplicates(keep = 'last', inplace = True)
                        #删除重复项【重要提示：由于未知原因，使用drop_duplicates依旧会出现重复，所以此处采用对索引进行判断，如果索引相同，则表示有重复】
                        if df.index.is_unique == False:
                            df = df[~df.index.duplicated(keep='last')]     #这里还有一个效率的问题，理论上旧数据不做去重，合并后再去重，但为了明确获取新老数据量的差别，因此做两次去重，降低一些效率
                            #print('合并后有重复项，去重')
                        #按照索引[日期]进行排序，升序
                        df = df.sort_index(ascending = True)
                        df = df[['open','close','high','low','volume','amount','turnoverratio','code']]
                        #df = df[~df.index.duplicated(keep='first')]
                        #总数据量
                        all_count = df.shape[0]
                        print('%s分钟线：%s读取完毕，新增数据量：%s条' % (min , code , all_count-old_count))
                        if all_count-old_count != 0:
                            #保存数据
                            df.to_csv('.\\data\\%smin\\%s.csv' % (min , code))
            else:
                #读取失败，说明目录无文件，直接写入
                #获取新数据并保存
                df_current = ts.get_k_data('%s' % (code), ktype = '%s' % (min))
                if df_current.empty == False:
                    df_current.set_index(['date'] , inplace = True)  
                    df_current.to_csv('.\\data\\%smin\\%s.csv' % (min , code))
                    print('%s分钟线：新增代码%s，数据量：%s条' % (min,code , df_current.shape[0]))
                else:
                    print('代码%s 无数据' % (code))


    def get_ETF_list(self , file_path = None):
        #设置ETF路径
        print('正在使用os.data_update中的获取ETF列表模块')
        if file_path == None:
            file_path = '.\\data\\ETF.csv'    
        #df=pd.read_csv(trade_log,dtype={'证券代码': np.str,'交收日期':np.str,'成交数量':np.int,'发生金额':np.float},encoding='gb18030')
        df=pd.read_csv(file_path , dtype = { '证券代码' : np.str , '名称' : np.str })
        return(df['证券代码'].tolist())
