# -*- coding: utf-8 -*-
import os
import pandas as pd
import tushare as ts
import numpy as np
from apt.os.data_update import Data_Update


def update_day():
    
    #获取第一个df
    df1 = ts.get_k_data('510050', start='2014-02-21',end='2014-04-01',ktype='D',autype='qfq')
    #重构索引
    df1.set_index(['date'], inplace = True)   
    #获取第二个df
    df2 = ts.get_k_data('510050', start='2014-01-01',end='2014-04-01',ktype='D',autype='qfq')
    #重构索引
    df2.set_index(['date'], inplace = True) 
    #两个dataframe合并
    df_new=pd.concat([df1, df2])
    #检查去重
    df_new = df_new.drop_duplicates()  
    #按照索引[日期]进行排序，升序
    print(df_new.sort_index(ascending = True))

    '''
    [更新30分钟数据]######
    函数说明 乔晖 2018/4/23
    具体步骤如下：
    1.获取每日开盘的数据，取得当日交易的股票列表
    2.从[5min]的文件夹中读取已有数据
    3.从[get_k_data]中读取新数据，存入临时文件夹并作读取动作 【此步骤因为目前无法为从文件读取的df和直接获取数据的df做去重处理】
    4.两者合并去重并排序
    5.写入原有文件
    
    '''
    ####步骤二：读取现有数据
    for code in code_list:
        try:
            df_old=pd.read_csv('./data/30min/%s.csv' % (code))
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
            df_new = ts.get_k_data('%s' % (code), ktype='30')
            df_new.set_index(['date'], inplace = True)  
            #新数据存盘
            df_new.to_csv('~/environment/TuShare/data/temp/%s_temp.csv' % (code))
            #重新读取新数据
            df_new=pd.read_csv('~/environment/TuShare/data/temp/%s_temp.csv' % (code))
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
            df.to_csv('~/environment/TuShare/data/30min/%s.csv' % (code))
            #总数据量
            all_count=df.shape[0]
            print('30分钟线：%s读取完毕，新增数据量：%s条' % (code,all_count-old_count))
        else:
            #读取失败，说明目录无文件，直接写入
            #获取新数据并保存
            df_current = ts.get_k_data('%s' % (code), ktype='30')
            df_current.set_index(['date'], inplace = True)  
            df_current.to_csv('~/environment/TuShare/data/30min/%s.csv' % (code))
            print('30分钟线：新增代码%s，数据量：%s条' % (code,df_current.shape[0]))

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
    
    '''
    ####步骤二：读取现有数据
    for code in code_list:
        try:
            df_old=pd.read_csv('.\\data\\%smin\\%s.csv' % (min,code))
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
            df.to_csv('.\\data\\%smin\\%s.csv' % (min,code))
            #总数据量
            all_count=df.shape[0]
            print('%s分钟线：%s读取完毕，新增数据量：%s条' % (min,code,all_count-old_count))
        else:
            #读取失败，说明目录无文件，直接写入
            #获取新数据并保存
            df_current = ts.get_k_data('%s' % (code), ktype='%s' % (min))
            df_current.set_index(['date'], inplace = True)  
            df_current.to_csv('.\\data\\%smin\\%s.csv' % (min,code))
            print('%s分钟线：新增代码%s，数据量：%s条' % (min,code,df_current.shape[0]))

def update_day(code_list=''):
    '''
    [更新日线数据]######
    函数说明 乔晖 2018/8/6
    具体步骤如下：
    1.从[get_k_data]中读取新数据并保存
    to_csv
    '''        
    for code in code_list:
        df=ts.get_k_data(code)    
        df.to_csv('.\\data\\day\\%s.csv' % (code))
     
            
def get_allcode():
    '''
    [获取全部代码]######
    函数说明 代码源自网络 2018/4/23
    '''    
    allcode=[]
    stock_info=ts.get_stock_basics()
    for i in stock_info.index:
        allcode.append(i)
    return allcode

def delete(code='510050'):
    df_old=pd.read_csv('.\data\60min\%s.csv' % (code))
    df_old.set_index(['date'], inplace = True)  
    
    print(df_old.drop_duplicates())


def update_today_all():
    '''
    [更新当日实时数据]######
    函数说明 乔晖 2018/4/23
    一次性获取当前交易所有股票的行情数据（如果是节假日，即为上一交易日，结果显示速度取决于网速）
    【行情不含基金和ETF】
    结果保存在/data/today_all.csv
    '''
    #修正乱码
    df=ts.get_today_all()
    df.to_csv('.\\data\\today_all.csv', encoding = 'utf_8_sig')
    
def load_today_all():
    '''
    [加载当日实时数据]######
    函数说明 乔晖 2018/4/25
    从硬盘中获取当日交易的数据，数据由update_today_all提供更新
    【行情不含基金和ETF】
    读取目录在/data/today_all.csv
    '''
    allcode=[]
    #载入代码
    df=pd.read_csv('.\\data\\today_all.csv')
    #筛选代码
    df.set_index(['code'], inplace = True) 
    for i in df.index:
        #补0后的代码
        idx = "%06d" % i
        #当前价格
        
        try:
            trade=float(df.loc[i,['trade']])
        except :
            trade=0
        #print("%s交易价格为%s" % (idx,trade))
        if trade==0:
            #未交易，不写入代码列表
            #print('%s未交易%s' % (idx,trade))
            allcode.append(idx)
        else:
            allcode.append(idx)
    return allcode
        
    
def get_allcode():
    allcode=[]
    stock_info=ts.get_stock_basics()
    #print(stock_info.shape[0])
    #print(stock_info)
    for i in stock_info.index:
        i=i.zfill(5)
        allcode.append(i)
        #print(i)
    return allcode

   
    
def update_all():
    '''
    [更新所有数据]######
    函数说明 乔晖 2018/4/25
    更新所有行情数据，目前包括5分钟/60分钟 
    【行情含基金和ETF】
    
    ETF特指以下基金列表['512880','510050','510180','510230','510300','510500','510880','510900','159901','159902','159915','159919','159920','159934','159937','159938','159949','159952','512980','512800','512880','512660','512680','512290','512580','512760','513500']
    '''
    #512710未上市
ETF_Trade=['512880','510050','510180','510230','510300','510500','510880','510900','159901','159902','159915','159919','159920','159934','159937','159938','159949','159952','512980','512800','512880','512660','512680','512290','512580','512760','513500','300033','600570','300059','300236','303976','159928']
#ETF_LIST=['501060','501070','601798']


#更新今日行情列表
#update_today_all()
#加载今日行情列表
code=load_today_all()

#从文件中获取ETF列表
update = Data_Update()
ETF_LIST = update.get_ETF_list()



#优先更新列表 用完请注释掉
update.update_day( ETF_Trade , filter_last = 0 )
#update.update_min( ETF_LIST , min = 15 )
#update.update_min( code , min = 15 )

#优先列表更新
#update.update_day( code , filter_last = 0 )
#update.update_min( code , min = 5 )


#ETF数据更新
update.update_day( ETF_LIST )
update.update_min( ETF_LIST , min = 5 )
update.update_min( ETF_LIST , min = 15 )
update.update_min( ETF_LIST , min = 30 )
update.update_min( ETF_LIST , min = 60 )
print('ETF处理完毕！')

#一般证券列表数据更新
update.update_day( code , filter_last = 0 )
update.update_min( code , min = 5 )
update.update_min( code , min = 15 )
update.update_min( code , min = 30 )
update.update_min( code , min = 60)
print('处理完毕！')

#update_day(['sh'])


#更新5分钟数据
#update_min(code,'5')
#print('5分钟处理完毕！')

#更新30分钟数据
#update_min(code,'30')
#print('30分钟处理完毕！')

#更新60分钟数据
#update_min(code,'60')
#print('60分钟处理完毕！')