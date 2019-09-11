# -*- coding: utf-8 -*-
import os
from datetime import datetime
import numpy as np
import pandas as pd
import tushare as ts
#指定日期间交易列表（有过交易的所有证券代码列表，如果买入卖出，股票空仓，也会在列表内）
daily_code_list=[]
'''
相关专有名词表（自定义）
持仓 open position
资金流动 cash flow
账面资金 net cash
账面资产 net asset
净值 fund value

'''
def get_trade_date(code='510300',start_date='2018-08-01'):
    #定义目录：读取510300的成交日期数据
    address='.\\data\\day\\%s.csv' % (code)
    df=pd.read_csv(address,dtype={'date': np.str})
    #日期筛选
    df=df[(df['date']>=start_date)]
    #返回交易日期
    df=df[['date']]
    #dataframe转series
    ts=pd.Series(df['date'].values)
    #series转化为list 备用返回方式
    #print(ts.values.tolist())
    return ts

def get_sh_data(start_date='2018-01-01'):
    #获取上证指数数据，以开始日期为基准进行矫正，用于基金业绩比较
    address='.\\data\\day\\sh.csv'
    df=pd.read_csv(address,dtype={'date': np.str})
    #日期筛选
    df=df[(df['date']>=start_date)]
    #基准日的收盘价，此为比较依据
    idx =df.index.tolist()
    base_value=df.ix[idx[0],'close'].astype(float)
    #增加基金比较基准
    df['base_value']=df['close']/base_value
    return df[['date','close','base_value']]


def get_transactions_info():
    #读取交割单信息
    trade_log='.\\trade\\2018_fund.csv'
    #df=pd.read_csv(trade_log,dtype={'证券代码': np.str,'交收日期':np.str,'成交数量':np.int,'发生金额':np.float},encoding='gb18030')
    df=pd.read_csv(trade_log,dtype={'证券代码': np.str,'交收日期':np.str,'成交数量':np.int,'发生金额':np.float})
    #交易日期时间序列化
    df['交收日期'] = pd.to_datetime(df['交收日期'],format='%Y%m%d') 
    return df

def get_close_data(start_date='2018-01-01',code_list=[]):
    #获取指定交易区间内，指定股票的收盘价矩阵
    #定义路径
    address='.\\data\\day'
    #定义交易日信息，index
    idx_date=get_trade_date(start_date=start_date)
    #创建空的表单
    df=pd.DataFrame(index=idx_date.values.tolist(),columns=code_list)
    for code in code_list:
        df_code=pd.read_csv('%s\\%s.csv' % (address,code))[['date','close']]
        #日期筛选 
        df_code=df_code[(df_code['date']>=start_date)]
        #重命名列
        df_code=df_code.rename(columns={'close':code})
        #重置索引
        df_code=df_code.set_index('date')
        #填充数据
        df=df.combine_first(df_code)
    return df

def get_net_asset_value_NA(start_date='2018-01-01'):
    #每日基金资产价格：持仓股数*收盘价
    ####停用####
    net_asset=get_net_asset(start_date)
    #print(net_asset)
    close_data=get_close_data(start_date,daily_code_list)
    df=net_asset*close_data
    print(df)
    return 


def get_net_asset(start_date='2018-01-01'):
    #每日基金持仓股数
    #1：读取基础信息
    #   1.1 读取交易日信息
    idx_date=get_trade_date(start_date=start_date)
    #   1.2 读取交割单信息
    df_transactions=get_transactions_info()
    #   1.3 筛选交割单信息，挑出符合的内容（按日期/交易性质）
    #df_transactions=df_transactions[(df_transactions['交收日期']>=start_date) & ((df_transactions['操作']=='证券卖出') | (df_transactions['操作']=='证券买入'))] 
    #   1.4 进行交易拆分和汇总
        #注1：原先交易是合并的，但后续查询交割单发现卖出交易中股数为正，系统认为是买入，所以需要修正
        #注2：原系统无法处理一天内分两笔买卖同一证券代码，因此需要进行汇总处理
    #买卖拆分
    df_transactions_buy=df_transactions[(df_transactions['交收日期']>=start_date) & (df_transactions['操作']=='证券买入') ] [['交收日期','证券代码','成交数量']]
    df_transactions_sell=df_transactions[(df_transactions['交收日期']>=start_date) & (df_transactions['操作']=='证券卖出')] [['交收日期','证券代码','成交数量']]
    #
    #df_transactions_sell['成交数量'] = df_transactions_sell.index
    #买卖汇总
    df_transactions_buy=df_transactions_buy.groupby(['交收日期','证券代码']).sum()
    df_transactions_sell=df_transactions_sell.groupby(['交收日期','证券代码']).sum()
    #print(df_transactions_sell)
    #df_transactions_sell=df_transactions_sell.reset_index(level='交收日期',inplace=True)
    #df_transactions_sell['证券代码'] = df_transactions_sell.index.get_level_values('证券代码')
    #df_transactions_sell=df_transactions_sell.drop_index(index='证券代码',inplace=True)
    #print(df_transactions_sell)
    #   1.5 汇总交易代码（用于后续通过pivot来定义有多少列及各列的列名）
    code_list= df_transactions.drop_duplicates(subset=['证券代码'],keep='first')['证券代码'].tolist()   
    #daily_code_list=code_list
    #2:创建交易记录df
    #   2.1 创建空记录
    #       行：交易日期;列：所有交易的代码列表    
    #df_trade_log=pd.DataFrame(index=idx_date.values.tolist(),columns=code_list)
    df_trade_log_buy=pd.DataFrame(index=idx_date.values.tolist(),columns=code_list)
    df_trade_log_sell=pd.DataFrame(index=idx_date.values.tolist(),columns=code_list)
    #   2.2 将筛选后的交割单转换成2.1中空记录表的形式
    #将交割单中的部分内容导入临时表单中
    #df_transac_list=df_transactions[['交收日期','证券代码','成交数量']]
    #df_transac_list_buy=df_transactions_buy[['交收日期','证券代码','成交数量']]
    #df_transac_list_sell=df_transactions_sell[['交收日期','证券代码','成交数量']]
    #强制类型转换（可做可不做）
    #df_transac_list[['交收日期','证券代码','成交数量']]=df_transactions[['交收日期','证券代码','成交数量']].astype(str)
    #将临时表中的证券代码分组，转换成新表中的列，形成以交易日期为索引，每个代码自成一列，显示每个交易日每个代码成交的数量
    #df_transac_list=df_transac_list.pivot(index='交收日期', columns='证券代码', values='成交数量')
    df_transac_list_buy=df_transactions_buy.pivot(index='交收日期', columns='证券代码', values='成交数量')
    df_transac_list_sell=df_transactions_sell.pivot(index='交收日期', columns='证券代码', values='成交数量')
    df_transac_list=df_transac_list_buy-df_transac_list_sell
    #print(df_transac_list)
    #3：创建每日持仓表单
    #   3.1 将交易记录表单标准化（nan数据置0）
    df_trade_log=df_trade_log.combine_first(df_transac_list)
    #   2.1.1 每日交易记录表=每日买入矩阵-每日卖出矩阵
    df_open_position=df_trade_log.fillna(0)
    #   3.2 进行数据累加计算（汇总）
    df_open_position=df_open_position.expanding(min_periods=1).sum()
    #4：计算每日持仓价值
    #   4.1 得到收盘价矩阵
    close_date=get_close_data(start_date=start_date,code_list=code_list)
    #   4.2 矩阵相乘 得到持仓价值
    asset_value=df_open_position*close_date
    #   4.3 持仓价值汇总
    asset_value['持仓金额'] = asset_value.apply(lambda x: x.sum(), axis=1)
    #sum_asset_value=
    #print(asset_value)
    #返回
    return asset_value['持仓金额']

def get_net_asset_V2(start_date='2018-01-01'):
    #每日基金持仓股数
    #V2修改内容如下：
    #1. 修正同一天多次卖出或者买入同一证券代码报错的问题
    #2. 修正卖出代码在数据处理上变成买入操作的问题
    #1：读取基础信息
    #   1.1 读取交易日信息
    idx_date=get_trade_date(start_date=start_date)
    #   1.2 读取交割单信息
    df_transactions=get_transactions_info()
    #   1.3 筛选交割单信息，挑出符合的内容（按日期/交易性质）
    df_transactions=df_transactions[(df_transactions['交收日期']>=start_date) & ((df_transactions['操作']=='证券卖出') | (df_transactions['操作']=='证券买入'))] 
    #   1.4 进行交易拆分和汇总
        #注1：原先交易是合并的，但后续查询交割单发现卖出交易中股数为正，系统认为是买入，所以需要修正
        #注2：原系统无法处理一天内分两笔买卖同一证券代码，因此需要进行汇总处理
    #买卖拆分
    df_transactions_buy=df_transactions[(df_transactions['交收日期']>=start_date) & (df_transactions['操作']=='证券买入') ] [['交收日期','证券代码','成交数量']]
    df_transactions_sell=df_transactions[(df_transactions['交收日期']>=start_date) & (df_transactions['操作']=='证券卖出')] [['交收日期','证券代码','成交数量']]
    #
    #df_transactions_sell['成交数量'] = df_transactions_sell.index
    #买卖汇总
    df_transactions_buy=df_transactions_buy.groupby(['交收日期','证券代码']).sum()
    df_transactions_sell=df_transactions_sell.groupby(['交收日期','证券代码']).sum()
    #汇总后由于变成了双索引，将所有索引重置，变成索引0,1,3,4 列为'交收日期','证券代码'，'成交数量'
    df_transactions_sell=df_transactions_sell.reset_index()
    #print(df_transactions_sell)
    #df_transactions_sell.set_index(['交收日期'], inplace=True)
    df_transactions_buy=df_transactions_buy.reset_index()
    df_transactions_buy.set_index('交收日期', inplace=True)
    #print(df_transactions_buy)
    #print(df_transactions_sell)
    #df_transactions_sell=df_transactions_sell.reset_index(level='交收日期',inplace=True)
    #df_transactions_sell['证券代码'] = df_transactions_sell.index.get_level_values('证券代码')
    #df_transactions_sell=df_transactions_sell.drop_index(index='证券代码',inplace=True)
    #print(df_transactions_sell)
    #   1.5 汇总交易代码（用于后续通过pivot来定义有多少列及各列的列名）
    code_list= df_transactions.drop_duplicates(subset=['证券代码'],keep='first')['证券代码'].tolist()   
    #daily_code_list=code_list
    #2:创建交易记录df
    #   2.1 创建空记录
    #       行：交易日期;列：所有交易的代码列表    
    df_trade_log=pd.DataFrame(index=idx_date.values.tolist(),columns=code_list)
    df_trade_log_buy=pd.DataFrame(index=idx_date.values.tolist(),columns=code_list)
    df_trade_log_sell=pd.DataFrame(index=idx_date.values.tolist(),columns=code_list)
    #   2.2 将筛选后的交割单转换成2.1中空记录表的形式
    #将交割单中的部分内容导入临时表单中
    df_transac_list=df_transactions[['交收日期','证券代码','成交数量']]
    df_transac_list_buy=df_transactions_buy[['证券代码','成交数量']]
    df_transac_list_sell=df_transactions_sell[['证券代码','成交数量']]

    #强制类型转换（可做可不做）
    #df_transac_list[['交收日期','证券代码','成交数量']]=df_transactions[['交收日期','证券代码','成交数量']].astype(str)
    #将临时表中的证券代码分组，转换成新表中的列，形成以交易日期为索引，每个代码自成一列，显示每个交易日每个代码成交的数量

    #df_transac_list=df_transac_list.pivot(index='交收日期', columns='证券代码', values='成交数量')


    
    df_transac_list_buy=df_transactions_buy.pivot( columns='证券代码', values='成交数量')
    df_transac_list_sell=df_transactions_sell.pivot(index='交收日期', columns='证券代码', values='成交数量')
    #df_transac_list2=df_transac_list_buy.fillna(0)-df_transac_list_sell.fillna(0)
    #3：创建每日持仓表单
    #   3.1 将交易记录表单标准化（nan数据置0）
    #df_trade_log=df_trade_log.combine_first(df_transac_list)
    df_trade_log_buy=df_trade_log_buy.combine_first(df_transac_list_buy).fillna(0)
    #买入矩阵
    #print('买入矩阵')
    #print(df_trade_log_buy)
    df_trade_log_sell=df_trade_log_sell.combine_first(df_transac_list_sell).fillna(0)
    #print('卖出矩阵')
    #   2.1.1 每日交易记录表=每日买入矩阵-每日卖出矩阵
    df_trade_log=df_trade_log_buy-df_trade_log_sell
    #print('买卖记录矩阵')
    #print(df_trade_log)
    df_open_position=df_trade_log.fillna(0)
    #   3.2 进行数据累加计算（汇总）
    df_open_position=df_open_position.expanding(min_periods=1).sum()
    #保存每日持仓股票数额数据
    df_open_position.to_csv('.\\trade\\df_open_position.csv', encoding='utf_8_sig')
    #4：计算每日持仓价值
    #   4.1 得到收盘价矩阵
    close_date=get_close_data(start_date=start_date,code_list=code_list)
    #   4.2 矩阵相乘 得到持仓价值
    asset_value=df_open_position*close_date
    #   4.3 持仓价值汇总
    asset_value['持仓金额'] = asset_value.apply(lambda x: x.sum(), axis=1)
    #sum_asset_value=
    #print(asset_value)
    #返回
    #return asset_value['持仓金额']
    return asset_value

def get_cash_flow(start_date='2018-01-01'):
    #每日基金现金流动情况
    # 计算交割单中的现金流动情况
    #1：读取基础信息
    #   1.1 读取交易日信息
    idx_date=get_trade_date(start_date=start_date)
    #   1.2 读取交割单信息
    df_transactions=get_transactions_info()
    #2:创建现金流量df
    #   2.1 创建空记录
    #       行：交易日期;列：发生金额（包含佣金），账面现金
    df_trade_log=pd.DataFrame(index=idx_date.values.tolist(),columns=['账面现金'])  
    #   2.2 筛选的交割单导入临时表单并按日期进行金额汇总
    #将交割单中的部分内容导入临时表单中
    df_transac_list=df_transactions[['交收日期','发生金额']]
    #按日期重新索引
    df_transac_list=df_transac_list.set_index('交收日期')
    #按日期进行金额汇总
    df_transac_list=df_transac_list.groupby('交收日期').sum()
    #print(df_transac_list)
    #   2.3 将交易记录表单标准化（nan数据置0）
    
    df_trade_log=df_trade_log.combine_first(df_transac_list)
    
    df_cash_flow=df_trade_log.fillna(0)
    print(df_cash_flow)
    #   2.4 进行数据累加计算（汇总）
    df_cash_flow=df_cash_flow.expanding(min_periods=1).sum()
    df_cash_flow['账面现金']=df_cash_flow['发生金额']

    #返回
    return df_cash_flow['账面现金']
def get_cash_flow_V2(start_date='2018-01-01'):
    #每日基金现金流动情况
    # 计算交割单中的现金流动情况
    #1：读取基础信息
    #   1.1 读取交易日信息
    idx_date=get_trade_date(start_date=start_date)
    #   1.2 读取交割单信息
    df_transactions=get_transactions_info()
    #2:创建现金流量df
    #   2.1 创建空记录
    #       行：交易日期;列：发生金额（包含佣金），'账面现金','基金申购','确认份额','基金份额'
    #       备注：份额计算由于涉及到前一日净值，因此不在现金流中计算，放入基金净值计算
    df_trade_log=pd.DataFrame(index=idx_date.values.tolist(),columns=['账面现金'])
    df_fund=pd.DataFrame(index=idx_date.values.tolist(),columns=['基金申赎','确认份额','基金份额'])
    #   2.2 进行基金份额处理
    #   筛选申购记录（申购金额为正，赎回金额为负）
    df_fund_purchase=df_transactions[(df_transactions['交收日期']>=start_date) & ((df_transactions['操作']=='证券转银行') | (df_transactions['操作']=='银行转证券'))][['交收日期','发生金额']] 
    #当日申购赎回记录进行汇总
    df_fund_purchase=df_fund_purchase.groupby(['交收日期']).sum()
    #插入总表
    df_fund['基金申赎']=df_fund.combine_first(df_fund_purchase)
    #print(df_fund)
    #   2.2 筛选的交割单导入临时表单并按日期进行金额汇总
    #将交割单中的部分内容导入临时表单中
    df_transac_list=df_transactions[['交收日期','发生金额']]
    #按日期重新索引
    df_transac_list=df_transac_list.set_index('交收日期')
    #按日期进行金额汇总
    df_transac_list=df_transac_list.groupby('交收日期').sum()
    #print(df_transac_list)
    #   2.3 将交易记录表单标准化（nan数据置0）
    
    df_trade_log=df_trade_log.combine_first(df_transac_list)
    
    df_cash_flow=df_trade_log.fillna(0)
    #print(df_cash_flow)
    #   2.4 进行数据累加计算（汇总）
    df_cash_flow=df_cash_flow.expanding(min_periods=1).sum()
    df_cash_flow['账面现金']=df_cash_flow['发生金额']
    df_cash_flow['基金申赎']=df_fund['基金申赎']
    #返回
    #return df_cash_flow[['账面现金','基金申赎']]
    return df_cash_flow

def get_fund_value(start_date='2018-01-01'):
    #每日净值计算 默认新开仓
    # 计算基金每日净值
    #1：读取基础信息
    #   1.1 读取交易日信息
    #idx_date=get_trade_date(start_date=start_date)
    #   1.2 读取交割单信息
    #df_transactions=get_transactions_info()
    #   1.1 读取现金流
    cash_flow=get_cash_flow_V2(start_date)
    #   1.2 读取持仓记录表
    net_asset=get_net_asset_V2(start_date)

    #2:创建基金净值df
    #   2.1 两表合并，建立新表：即基金净值总表
    #       行：交易日期;列：申赎金额，基金份额，账面现金，持仓金额，总资产，净值，业绩比较基准(沪深300ETF)
    fund_value=pd.concat([net_asset,cash_flow],axis=1)
    fund_value['总资产']=fund_value['持仓金额']+fund_value['账面现金']
    #       增加'份额确认','基金份额',净值 三列
    col_len=len(fund_value.columns)
    fund_value.insert(col_len, '份额确认',np.nan)
    fund_value.insert(col_len+1, '基金份额',np.nan)
    fund_value.insert(col_len+2, '基金净值',np.nan)
    #数据初始化
    fund_value.ix[0, '基金净值']=1
    fund_value.ix[0, '基金份额']=0
    fund_value=fund_value.fillna(0)
    #   2.2 逐行扫描进行份额和基金净值计算（目前技术条件只能采取历遍而非矩阵操作）
    #由于性能考虑，需要跳过首行进行处理，因此list写入序列进行迭代
        #计算公式：
        #净值A=当日基金份额B/当日基金总资产C
        #份额确认D=当日申购金额E/前一日基金净值A.-1
        #基金份额B=前一日基金份额B.-1+当日基金确认份额D （本规则下当日申购资金直接确认，可当日进行买入交易，为T+0操作）   
    iteridx = iter(fund_value.index.tolist())
    #跳一行
    next(iteridx)
    #初始化前一日信息
    pre_shares=0
    pre_values=1
    for i in iteridx:
        #时间格式转换为字符串
        i=i.strftime('%Y-%m-%d')
        #判断基金有无申赎，有：进行份额确认；无：份额维持上一日
        #计算公式：
        #净值A=当日基金份额B/当日基金总资产C
        #份额确认D=当日申购金额E/前一日基金净值A.-1
        #基金份额B=前一日基金份额B.-1+当日基金确认份额D （本规则下当日申购资金直接确认，可当日进行买入交易，为T+0操作）        
        if fund_value.ix[i, '基金申赎']==0:
            #无申赎
            
            fund_value.ix[i, '份额确认']=0
            fund_value.ix[i, '基金份额']=pre_shares
            if fund_value.ix[i, '总资产']==0:
                fund_value.ix[i, '基金净值']=1
            else:
                fund_value.ix[i, '基金净值']=fund_value.ix[i, '总资产']/fund_value.ix[i, '基金份额']
        else:
            #有申购，总资产不可能为0，因此不需要进一步判断
            fund_value.ix[i, '份额确认']=fund_value.ix[i, '基金申赎']/pre_values
            fund_value.ix[i, '基金份额']=fund_value.ix[i, '份额确认']+pre_shares
            fund_value.ix[i, '基金净值']=fund_value.ix[i, '总资产']/fund_value.ix[i, '基金份额']
            
        #写入今日信息，变成下一个循环的昨日信息
        pre_shares=fund_value.ix[i, '基金份额']
        pre_values=fund_value.ix[i, '基金净值']
        #print(pre_values)

        

            
        
    #fund_value['基金净值']=fund_value['账面现金'].shift(1)/10
    
    #fund_value['基金净值']=(fund_value['基金份额'].shift(1)+fund_value['份额确认']/fund_value['基金净值'].shift(1))/fund_value['总资产']
    #fund_value.iat[0,'基金份额']=0
    #fund_value.iat[0,'基金净值']=1

    #print(fund_value['总资产'])
    #print('基金净值矩阵')
    print(fund_value[['账面现金','总资产','基金申赎','份额确认','基金份额','基金净值']])

    fund_value.to_csv('.\\trade\\fund_value.csv', encoding='utf_8_sig')
    #   2.2 表单整合，将现金流量表和持仓表格整合进入
    #   2.3 填充基础信息
    '''
    df_trade_log=pd.DataFrame(index=idx_date.values.tolist(),columns=['账面现金'])
    
    #   2.2 筛选的交割单导入临时表单并按日期进行金额汇总
    #将交割单中的部分内容导入临时表单中
    df_transac_list=df_transactions[['交收日期','发生金额']]
    #按日期重新索引
    df_transac_list=df_transac_list.set_index('交收日期')
    #按日期进行金额汇总
    df_transac_list=df_transac_list.groupby('交收日期').sum()
    #   2.3 将交易记录表单标准化（nan数据置0）
    
    df_trade_log=df_trade_log.combine_first(df_transac_list)
    df_cash_flow=df_trade_log.fillna(0)
    #   2.4 进行数据累加计算（汇总）
    df_cash_flow=df_cash_flow.expanding(min_periods=1).sum()
    df_cash_flow['账面现金']=df_cash_flow['发生金额']
    df_cash_flow.to_csv('.\\trade\\fund_value.csv')
    #返回
    '''


get_fund_value(start_date='2017-12-10')

#print(get_sh_data('2017-12-10'))
'''
净值-持仓计算
net_asset=get_net_asset('2018-04-01')
print(net_asset)
close_date=get_close_data(start_date='2018-04-01',code_list=['510300','510050'])
print(close_date)
fund_value=net_asset*close_date
print(fund_value)
'''



#print(idx_date['date'])
#print(df)

#print(df[df['操作']=='银行转证券'])
#print(df[df['操作']=='银行转证券'])

#print( pd.to_datetime(df['交收日期']))

#df['交收日期']=df['交收日期'].apply(lambda x:datetime.strptime(x,'%Y%M%D'))
#print(df['交收日期'])
#print(df[df['操作']=='银行转证券'])

#字符串日期转换成datetime
'''
df_date=pd.DataFrame(['20180101','20180102'],columns=['日期'])
print(df_date)
df_date['日期'] = pd.to_datetime(df_date['日期'])
print(df_date)
'''
#######################
#master
