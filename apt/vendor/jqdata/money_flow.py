import numpy as np
import pandas as pd
import tushare as ts
import sqlalchemy
import datetime
from jqdatasdk import *
from apt.vendor.jqdata.base import base as base

class money_flow(base):
    """
    专门处理资金流向的类
    """
    def daily_update(self , code_list =  None , start_date = datetime.datetime(2005,1,1) , end_date = datetime.datetime.now()):
        """
        每日资金流向更新
        """
        #获取更新列表
        if code_list == None:
            #更新列表未填写，则默认为空，即全部更新
            code_list = list(get_all_securities(['stock'],date = end_date).index)
        #打印标题
        print("############正在准备更新资金流向信息###########")
        """
        更新逻辑：
            1. 取出所有的stock列表，进行单代码循环
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
        for code in code_list:
            #获取数据库中存在的数据最后更新日期（加入强制使用索引的内容）
            query2 = f"select date FROM jqdata_money_flow FORCE INDEX (main) WHERE date BETWEEN '{start_date.date()}' and '{end_date.date()}' and code = '{code}' ORDER BY date DESC LIMIT 1" 
            df_db = pd.read_sql_query(query2 , self.engine)
            if df_db.empty == True:
                #数据库不存在数据
                new_start_date = start_date
            else:
                #数据库存在数据，新定义开始日期（数据库最后一天+1）
                new_start_date =  df_db.loc[0 , 'date']  + datetime.timedelta(days=1)         
            df_flow = get_money_flow(security_list = code , start_date = new_start_date, end_date = end_date)
            #重命名列（money_flow中的证券代码sec_code和数据库中的不一致）
            df_flow.rename(columns = {'sec_code':'code'} , inplace = True)
            #print(df_flow)
            #保存至数据库 
            if df_flow.empty == True:
                print("%s 进行差集处理后剩余数据为空或者jqdata无数据，跳过上传" % (code))
            else:
                df_flow.to_sql(
                        name = 'jqdata_money_flow',
                        con = self.engine,
                        index = False,
                        if_exists = 'append')
                print("%s 数据已上传完成(money flow)" % (code))

if __name__=="__main__":
    money = money_flow()
    start = datetime.datetime(2021,1,1)
    end = datetime.datetime.now() #2020年数据已完成更新
    df_remain = get_query_count()
    print(df_remain)
    money.daily_update( start_date = start , end_date =end)
    df_remain = get_query_count()
    print(df_remain)