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
    def update_fund_share_daily(self , type = 'etf' , start_date = datetime.datetime(2005,1,1) , end_date = datetime.datetime.now()):
        """
        更新每日ETF净值信息
        start_date 开始日期 默认2020/1/1
        end_date 结束日期 默认当前时间
        type：etf/lof 默认为etf
        """
        #获取更新列表
        code_list = list(get_all_securities(types = type , date = end_date).index)
        #打印标题
        print("############正在准备更新基金（ETF/LOF）每日净值信息###########")
        print(f"当前{type}共有{len(code_list)}只基金")
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
                print("%s 区间数据为空，跳过上传" % (code))
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

    def get_etf_daily(self , code = None , day = datetime.datetime.now() , min_money = 0 , min_share = 0):
        """
        获取指定日期的ETF场内交易基金的成交量情况
        输入：
            code 证券代码
            day 取数据的基准日期 默认是当天
            min_money ETF基金当日成交量的最小值
            min_share ETF基金当日份额的最小值
        返回：
            
        """
        #选取基金份额大于2亿 每日成交额大于5千万的场内ETF基金
        sql = f("""
                SELECT
	            sr. CODE,
	            sr. NAME,
	            sr.date,
	            d.close,
	            convert(sr.shares / 1e8, decimal(12,1))  as "基金份额(亿)",
	            convert(d.money / 1e8, decimal(12,1)) as "成交额(亿)"
            FROM
	            fund_share_daily sr,
	            jqdata_1d d
            WHERE
	            d.date = sr.date
            AND d. CODE = sr. CODE
            AND sr.date = '2021/9/24'
            AND d.money >= 5e7
            and sr.shares >=2e8
        """)
        print(sql)
