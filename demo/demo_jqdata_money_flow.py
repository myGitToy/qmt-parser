from jqdatasdk import *
import pandas as pd
import datetime
import sqlalchemy
from apt.vendor.jqdata.jqdata import jqdata as jqdata
from apt.vendor.jqdata.ETF import ETF as ETF

def update_fund_share_daily( start_date = datetime.datetime(2005,1,1) , end_date = datetime.datetime.now()):
    """
    更新每日ETF净值信息
    start_date 开始日期 默认2020/1/1
    end_date 结束日期 默认当前时间
    """
    #获取更新列表
    code_list = list(get_all_securities(['etf'] , date = end_date).index)
    #打印标题
    print("############正在准备更新ETF每日净值信息###########")
    print("当前ETF共有%s支基金" % len(code_list))

    """
    更新逻辑：
        1. 取出所有的ETF列表，进行单代码循环
        2. 取出该代码在数据库中，指定日期间的最后更新日期
            2.1 为空，则全部更新
            2.2 不为空，则取出最后日期，以这个日期为基准，进行更新
        3. 

    """
    for code in code_list:
        #获取数据库中存在的数据最后更新日期
        query = "select date FROM fund_share_daily WHERE date BETWEEN '%s' and '%s' and code = '%s' ORDER BY date DESC LIMIT 1" % ( start_date.date() , end_date.date() , code )
        df_db = pd.read_sql_query(query , self.engine)
        if df_db.empty == True:
            #数据库不存在数据
            new_start_date = start_date
            print(new_start_date )
            print(end_date)
        else:
            #数据库存在数据，新定义开始日期
            new_start_date = df_db.loc[0 , 'date']  

        df2 = finance.run_query(query(finance.FUND_SHARE_DAILY).filter(finance.FUND_SHARE_DAILY.date=='2019-05-23').limit(1))
        print(df_jqdata)
        get_bars(security = code , count = count_suppose , unit = ktype , fields = ['date', 'open', 'close', 'high', 'low', 'volume', 'money','factor'] , include_now = False , end_dt = end_date , df = True)
        df_jqdata['code'] = code
        #print(df_jqdata)
        #数据去重（因为停盘的关系，比如获取1/1-1/30号的数据，实际通过count取到的数据可能包含前面12月份的，直接写入因为唯一索引的约束，会报错）
        if  ktype == '1d':
            #日线数据特殊处理，因为数据库中的格式是date，不是datetime
            df_jqdata = df_jqdata[(df_jqdata.date >= start_date.date()) & (df_jqdata.date <= end_date.date())]
        else:
            #分时数据正常处理
            df_jqdata = df_jqdata[(df_jqdata.date >= start_date) & (df_jqdata.date <= end_date)]
        #数据去除NA（在极特殊的情况下会引发异常 数据库字段NOT NULL 冲突）
        df_jqdata.dropna(inplace = True)
        #检索数据库中的数据
        query2 = "select date from jqdata_%s where code = '%s' and left(date,10) BETWEEN '%s' and '%s'" % (ktype , code , start_date.strftime("%Y-%m-%d") , end_date.strftime("%Y-%m-%d"))         
        df_db = pd.read_sql_query(query2 , self.engine)
        #将新老库合并，求差集
        df_jqdata = df_jqdata.append(df_db)
        df_jqdata.drop_duplicates(subset = ['date'] , keep = False ,inplace = True)
        #print(df_jqdata)
        #保存至数据库
        if df_jqdata.empty == True:
            print("%s 进行差集处理后剩余数据为空或者jqdata无数据，跳过上传" % (code))
        #print(df)
        else:
            df_jqdata.to_sql(
                    name = 'jqdata_%s' % (ktype),
                    con = self.engine,
                    index = False,
                    if_exists = 'append')
            print("%s 数据已上传完成(%s)" % (code,ktype))



#显示所有列
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
auth('13817092632','JQ@tushare123')
#获取全部
#df = get_money_flow(['300142.XSHE'], start_date='2020-6-16', end_date='2020-9-16', fields=None, count=None)
#获取大单date     sec_code  change_pct  net_amount_main  net_pct_main
#df = get_money_flow(['002647.XSHE'], start_date='2020-9-22', end_date='2020-12-07', fields=['date','change_pct','net_amount_main','net_pct_main'], count=None)
#df['net_pct_main_ma']=df['net_pct_main'].rolling(5).mean()
#print(df)
#查询场内基金每日份额
#df_fund=finance.run_query(query(finance.FUND_SHARE_DAILY).filter(finance.FUND_SHARE_DAILY.date=='2020-12-07' , finance.FUND_SHARE_DAILY.code=='159949.XSHG').limit(10))
start = datetime.datetime(2019,1,1)
end = datetime.datetime(2020,12,8)
print(start)
print(start.date())
code = '511220.XSHG'
#df = finance.run_query(query(finance.FUND_SHARE_DAILY).filter(finance.FUND_SHARE_DAILY.date=='2019-05-23').limit(100))
#print(df)
df_fund = finance.run_query(query(finance.FUND_SHARE_DAILY).filter(finance.FUND_SHARE_DAILY.date>= start.date() , finance.FUND_SHARE_DAILY.date<=  datetime.datetime.now().date() ,finance.FUND_SHARE_DAILY.code==code ))
print(df_fund)

#测试基金净值模块
e = ETF()
e.update_fund_share_daily(start_date = start , end_date = end)


