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
        print("当前ETF共有%s只基金" % len(code_list))
        """
        更新逻辑：
            1. 取出所有的ETF列表，进行单代码循环
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
            #获取数据库中存在的数据最后更新日期
            query2 = "select date FROM fund_share_daily WHERE date BETWEEN '%s' and '%s' and code = '%s' ORDER BY date DESC LIMIT 1" % ( start_date.date() , end_date.date() , code )
            df_db = pd.read_sql_query(query2 , self.engine)
            if df_db.empty == True:
                #数据库不存在数据
                new_start_date = start_date
            else:
                #数据库存在数据，新定义开始日期（数据库最后一天+1）
                new_start_date =  df_db.loc[0 , 'date']  + datetime.timedelta(days=1)         
            df_share = finance.run_query(query(finance.FUND_SHARE_DAILY).filter(finance.FUND_SHARE_DAILY.date >= new_start_date , finance.FUND_SHARE_DAILY.date <= end_date , finance.FUND_SHARE_DAILY.code == code ))
            #print(df_share)
            #保存至数据库
            if df_share.empty == True:
                print("%s 进行差集处理后剩余数据为空或者jqdata无数据，跳过上传" % (code))
            else:
                df_share.to_sql(
                        name = 'fund_share_daily',
                        con = self.engine,
                        index = False,
                        if_exists = 'append')
                print("%s 数据已上传完成(share)" % (code))

    def check_share_change(self , code = None , start_date = datetime.datetime(2005,1,1) , end_date = datetime.datetime.now()):
        """
        场内基金每日份额变化
        输入：
            code 证券代码
            start_date 开始日期
            end_date 结束日期

        返回：
            
        """


