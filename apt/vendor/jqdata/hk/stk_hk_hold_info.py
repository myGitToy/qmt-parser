import numpy as np
import pandas as pd
import tushare as ts
import sqlalchemy
import datetime
from jqdatasdk import *
from apt.vendor.jqdata.base import base as base
#from apt.vendor.jqdata.stk import stk as stk

class STK_HK_HOLD_INFO(base):
    """
    STK_HK_HOLD_INFO 沪深港通持股数据 / 上市至今，交易日20:30-06:30更新
    每次获取上限3000条
    """
    def daily_update(self , link_id =  ['310001','310002','310003','310004','310005'] , start_date = datetime.datetime(2005,1,1) , end_date = datetime.datetime.now()):
        """
        沪深港通持股数据 

        """
        #打印标题
        print("############正在准备沪深港通资金流向信息###########")
        """
        更新逻辑：
            1. 取出开始和结束日期
            2. 查询数据库中的最后更新日期
            3. 在此基础上+1 ，得到中间的交易天数
            4. 按每个交易日取出所有的数据（所有股票）
            5. 数据写入数据库
        逻辑优点和不足：
            1. 按天更新 每日更新全部代码，不做细分的代码区分
            2. 可以解决日常更新中，有部分日期重复的问题，比如每月的更新开始周期设定为1号，但5号更新是会自动过滤1-4号的数据
            3. 上述第二条还有一个很重要的应用场景：因为是指定区间的更新取最后一天，因此如果先更新了2020年的数据，随后再要更新2019年的数据，
                在这种情况下也是可以的，因为取的是区间最后一天，因此2019全年的数据也是空，也就会全部读取和更新
        """
        for link in link_id:
            #获取数据库中存在的数据最后更新日期（加入强制使用索引的内容）
            query2 = f"select date FROM stk_hk_hold_info FORCE INDEX (main) WHERE date BETWEEN '{start_date.date()}' and '{end_date.date()}' and link_id = '{link}' ORDER BY date DESC LIMIT 1" 
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
                df_flow = finance.run_query(query(finance.STK_HK_HOLD_INFO).filter(finance.STK_HK_HOLD_INFO.day == day , finance.STK_HK_HOLD_INFO.link_id == link))
                #重命名列（沪港通中的日期day和数据库中的不一致）
                df_flow.rename(columns = {'day':'date'} , inplace = True)
                #print(df_flow)
                #保存至数据库 
                if df_flow.empty == True:
                    print(f"{link}当日({day})无数据")
                else:
                    df_flow.to_sql(
                            name = 'stk_hk_hold_info',
                            con = self.engine,
                            index = False,
                            if_exists = 'append')
                    print(f"{day}数据已上传完成({link})")
    def delete_null(self):
        """
        负责处理异常数据
        https://huiqiao.visualstudio.com/MyFunds/_boards/board/t/MyFunds%20Team/Backlog%20items/?workitem=204

        """
        query2 = f"delete from jqdata_money_flow where (net_pct_s is null or net_amount_s is NULL) and date >='2021/1/1'" 
        df_db = pd.read_sql_query(query2 , self.engine)
        #print(df_db)
if __name__=="__main__":
    #此模块用于历史数据的更新，目前2021年前的数据已完成更新，因此模块下架停止使用
    money = STK_HK_HOLD_INFO()
    start = datetime.datetime(2014,1,1)
    end = datetime.datetime(2017,12,31) #2020年数据已完成更新
    df_remain = get_query_count()
    print(df_remain)
    money.daily_update( start_date = start , end_date =end)
    df_remain = get_query_count()
    print(df_remain)