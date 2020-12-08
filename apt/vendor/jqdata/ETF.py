import numpy as np
import pandas as pd
import tushare as ts
import sqlalchemy
import datetime
from jqdatasdk import *
from apt.vendor.jqdata.base import base as base

class ETF(base):
    """
    专门处理ETF的类
    """
    def update_fund_share_daily(self , start_date = datetime.datetime(2005,1,1) , end_date = datetime.datetime.now()):
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
            query2 = "select date FROM fund_share_daily WHERE date BETWEEN '%s' and '%s' and code = '%s' ORDER BY date DESC LIMIT 1" % ( start_date.date() , end_date.date() , code )
            df_db = pd.read_sql_query(query2 , self.engine)
            if df_db.empty == True:
                #数据库不存在数据
                new_start_date = start_date
            else:
                #数据库存在数据，新定义开始日期
                new_start_date = df_db.loc[0 , 'date']  

            df_share = finance.run_query(query(finance.FUND_SHARE_DAILY).filter(finance.FUND_SHARE_DAILY.date >= new_start_date , finance.FUND_SHARE_DAILY.date <= end_date , finance.FUND_SHARE_DAILY.code == code ))
            #保存至数据库
            if df_share.empty == True:
                print("%s 进行差集处理后剩余数据为空或者jqdata无数据，跳过上传" % (code))
            #print(df)
            else:
                df_share.to_sql(
                        name = 'fund_share_daily',
                        con = self.engine,
                        index = False,
                        if_exists = 'append')
                print("%s 数据已上传完成(share)" % (code))

