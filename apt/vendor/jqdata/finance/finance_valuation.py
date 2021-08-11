import pandas as pd
import sqlalchemy
import datetime
from jqdatasdk import *
from apt.vendor.jqdata.base import base as base

class finance_valuation(base):
    """
    估值数据 / 2005至今，交易日18:00-24:00更新
    为了防止返回数据量过大, 我们每次最多返回10000行
    """
    def daily_update(self ,  start_date = datetime.datetime(2005,1,1) , end_date = datetime.datetime.now()):
        """
        每日估值数据更新
        按天更新模式（非按代码）
        """
        print("############正在准备更新估值信息###########")
        """
        更新逻辑：
            按天，和龙虎榜的逻辑一致

        """
        #获取数据库中存在的数据最后更新日期（加入强制使用索引的内容）
        query2 = f"select date FROM valuation WHERE date BETWEEN '{start_date.date()}' and '{end_date.date()}'  ORDER BY date DESC LIMIT 1" 
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
            df_flow = get_fundamentals(query(valuation),day)
            #重命名列（billboard_list中的日期列day和数据库中的不一致）
            df_flow.rename(columns = {'day':'date'} , inplace = True)
            #保存至数据库 
            if df_flow.empty == True:
                print("当天数据为空（不太可能，程序可能出错）")
            else:
                df_flow.to_sql(
                        name = 'valuation',
                        con = self.engine,
                        index = False,
                        if_exists = 'append')
                print("%s 数据已上传完成valuation)" % (day))

if __name__=="__main__":
    #此模块用于历史数据的更新，目前已完成历史数据更新
    #测试数据
    val = finance_valuation()
    #val.daily_update()
    start = datetime.datetime(2019,1,1)
    end = datetime.datetime.now()
    val.daily_update(start_date = start , end_date = end)
