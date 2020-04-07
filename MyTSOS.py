# -*- coding: utf-8 -*-
'''
【tushare os系统】
所有涉及到文档读取 处理的代码归类到TSOS来处理，包括交割单、K线，历史分笔数据处理等等

get_ETF_list
    从CSV文件中读取EFT列表，该列表定期更新


'''
from datetime import datetime,timedelta
import numpy as np
import pandas as pd
import tushare as ts
import logging
import os

def update_min(code_list='',min=''):
    '''
    [更新XX分钟数据]######
    函数说明 乔晖 2018/4/23

    具体步骤如下：
    1.获取每日开盘的数据，取得当日交易的股票列表
    2.从[5min]的文件夹中读取已有数据
    3.从[get_k_data]中读取新数据，存入临时文件夹并作读取动作 【此步骤因为目前无法为从文件读取的df和直接获取数据的df做去重处理】
    4.两者合并去重并排序
    5.写入原有文件

    更新记录：
        2018/4/23 
        1. 第一版文档完成    
    '''
    ####步骤二：读取现有数据
    for code in code_list:
        #数据补零
        code=code.zfill(6)
        try:
            df_old=pd.read_csv('.\\data2\\%smin\\%s.csv' % (min,code))
            success=True
        except IOError:
            #没有找到文件
            #print('error')
            success=False

        else:
            #读取成功
            pass
        if success:
            #读取成功，进行合并操作
            #处理旧数据
            df_old.set_index(['date'], inplace = True)  
            #旧数据量
            old_count=df_old.shape[0]
            #获取新数据
            df_new = ts.get_k_data('%s' % (code), ktype='%s' % (min))
            df_new.set_index(['date'], inplace = True)  
            #新数据存盘
            df_new.to_csv('.\\data\\temp\\%s_temp.csv' % (code))
            #重新读取新数据
            df_new=pd.read_csv('.\\data\\temp\\%s_temp.csv' % (code))
            df_new.set_index(['date'], inplace = True)  
            #删除临时文件 
            #目前无法进行删除操作，错误信息： No such file or directory: '~/environment/TuShare/data/temp/510300_temp.csv'
            #处理方法：建立/data/temp临时文件夹，存放临时文件，不做删除处理
            #os.remove('~/environment/TuShare/data/temp/%s_temp.csv' % (code))
            ###两个dataframe合并
            df=pd.concat([df_old, df_new],sort=True)
            #检查去重
            df = df.drop_duplicates() 
            #按照索引[日期]进行排序，升序
            df=df.sort_index(ascending = True)
            #保存数据
            df.to_csv('.\\data2\\%smin\\%s.csv' % (min,code))
            #总数据量
            all_count=df.shape[0]
            print('%s分钟线：%s读取完毕，新增数据量：%s条' % (min,code,all_count-old_count))
        else:
            #读取失败，说明目录无文件，直接写入
            #获取新数据并保存
            df_current = ts.get_k_data('%s' % (code), ktype='%s' % (min))
            df_current.set_index(['date'], inplace = True)  
            df_current.to_csv('.\\data2\\%smin\\%s.csv' % (min,code))
            print('%s分钟线：新增代码%s，数据量：%s条' % (min,code,df_current.shape[0]))

def get_ETF_list(file_path = None):
    #设置ETF路径
    if file_path == None:
        file_path='.\\data\\ETF.csv'    
    #df=pd.read_csv(trade_log,dtype={'证券代码': np.str,'交收日期':np.str,'成交数量':np.int,'发生金额':np.float},encoding='gb18030')
    df=pd.read_csv(file_path,dtype={'证券代码': np.str,'名称':np.str})
    return(df['证券代码'].tolist())
    #输出交割单信息

#get_ETF_list()
if __name__=="__main__":
    update_min(['501040','501041'],60)

