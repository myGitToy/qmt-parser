from jqdatasdk import *
from apt.vendor.jqdata.jqdata import data
from apt.vendor.jqdata.base import base as base
import pandas as pd
import datetime
import sqlalchemy

class VSI(base):
    def test(self , start = datetime.datetime(2021,1,1) , end = datetime.datetime.now()):
        #获取板块信息
        #######1. 加载不同的自选股列表（数据更新时不能打开相关的excel文件，否则读取权限会显示失败）
        code_list = data.read_excel(file_name = '.\\data\\海龟模型\\自选股列表.xlsx' , sheet_name = '33指数')['证券代码'].tolist()
        for code in code_list:
            sql_string = f"""
			SELECT v. CODE,v.date,d.high,d.low,d. OPEN,d. CLOSE,v.turnover_ratio,v.market_cap,v.circulating_market_cap
		FROM
			valuation v,jqdata_1d d
		WHERE
			v. CODE = d. CODE
			AND v.date = d.date
			and v.date between '2021/1/1' and '2021/8/1'
			AND v. CODE = '{code}'
		ORDER BY
			v.date DESC"""
            df_db = pd.read_sql_query(sql_string , self.engine)
            if df_db.empty == True:
                #数据库不存在数据
                new_start_date = start_date
            else:
                print(df_db)

if __name__ == '__main__':    
    start = datetime.datetime(2021,1,1)
    end = datetime.datetime.now()
    vsi = VSI(myauth = False)
    vsi.test(start = start , end = end)