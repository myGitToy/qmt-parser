import numpy as np
import pandas as pd
import tushare as ts
import sqlalchemy
import datetime
from jqdatasdk import *
from apt.vendor.jqdata.base import base as base

class billboard_list(base):
    """
    专门处理龙虎榜的类
    """
    def daily_update(self , code_list =  None , start_date = datetime.datetime(2005,1,1) , end_date = datetime.datetime.now()):
        """
        每日龙虎榜更新
        """
        #获取更新列表(目前按照天来更新，不需要正确代码列表)
        if code_list == None:
            #更新列表未填写，则默认为空，即全部更新
            pass
            #code_list = list(get_all_securities(['stock'] , date = end_date).index)
        #打印标题
        print("############正在准备更新龙虎榜信息###########")
        """
        更新逻辑：
            1. 取出开始和结束日期
            2. 查询数据库中的最后更新日期
            3. 在此基础上+1 ，得到中间的交易天数
            4. 按每个交易日取出所有的数据（所有股票）
            取出所有的stock列表，进行单代码循环
            2. 取出该代码在数据库中，指定日期间的最后更新日期
                2.1 为空，则全部更新
                2.2 不为空，则取出最后日期，以这个日期为基准，进行更新
            3. 数据写入数据库
        逻辑优点和不足：
            1. 单循环运行效率较高
            2. 可以解决日常更新中，有部分日期重复的问题，比如每月的更新开始周期设定为1号，但5号更新是会自动过滤1-4号的数据
            3. 上述第二条还有一个很重要的应用场景：因为是指定区间的更新取最后一天，因此如果先更新了2020年的数据，随后再要更新2019年的数据，
                在这种情况下也是可以的，因为取的是区间最后一天，因此2019全年的数据也是空，也就会全部读取和更新
            4. 这里写入时没有做去重，可能还是会触发唯一性约束错误（可能性低于0.01%）
        """
        #获取数据库中存在的数据最后更新日期（加入强制使用索引的内容）
        query2 = f"select date FROM jqdata_billboard_list FORCE INDEX (main) WHERE date BETWEEN '{start_date.date()}' and '{end_date.date()}'  ORDER BY date DESC LIMIT 1" 
        df_db = pd.read_sql_query(query2 , self.engine)
        if df_db.empty == True:
            #数据库不存在数据
            new_start_date = start_date
        else:
            #数据库存在数据，新定义开始日期（数据库最后一天+1）
            new_start_date =  df_db.loc[0 , 'date']  + datetime.timedelta(days=1)   
        #获取修正后的日期间隔里的交易日期
        day_list = get_trade_days(start_date = new_start_date , end_date = end_date)
        for day in day_list:
            df_flow = get_billboard_list(start_date = day, end_date = day)
            #重命名列（billboard_list中的日期列day和数据库中的不一致）
            df_flow.rename(columns = {'day':'date'} , inplace = True)
            #print(df_flow)
            #保存至数据库 
            if df_flow.empty == True:
                print("当天数据为空（不太可能，程序可能出错）")
            else:
                df_flow.to_sql(
                        name = 'jqdata_billboard_list',
                        con = self.engine,
                        index = False,
                        if_exists = 'append')
                print("%s 数据已上传完成billboard_list)" % (day))
if __name__=="__main__":
    auth('13817092632','JQ@tushare123')
    #显示所有列
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    #df=get_billboard_list(start_date = '2021-04-09', end_date = '2021-04-09')
    #print (df)
    money = billboard_list()
    start = datetime.datetime(2010,1,1)
    end = datetime.datetime.now() #2020年数据已完成更新
    df_remain = get_query_count()
    print(f"更新条目数{df_remain}")
    #money.delete_null()
    money.daily_update( start_date = start , end_date =end)
    df_remain = get_query_count()
    print(df_remain)