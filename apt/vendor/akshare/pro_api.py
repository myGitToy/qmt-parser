# -*- coding: utf-8 -*-
from datetime import datetime,date,timedelta
from apt.vendor.tspro.data import data as data
from apt.vendor.akshare.data import data as ak_data
import tushare as ts
import akshare as ak
import pandas as pd
import numpy as np
import pandas as pd

class pro_api(data):
    """
    akshare数据接口层，调用方法请参看task 449
    https://huiqiao.visualstudio.com/MyFunds/_sprints/taskboard/MyFunds%20Team/MyFunds/2023Q1?workitem=449
    """
    def __init__(self):
        #初始化 接入token
        self.pro = ts.pro_api("55297f16c0119146589e059db315ba28a9412e89ec9f91e538e655b2")
        self.token2 = '12345'
    
    def function_A(self):
        print('function_A')


        
class ths(pro_api):
    """
    同花顺概念接口层，调用方法请参看task 
    """


    def __init__(self):
        #使用super继承上级
        super(pro_api , self).__init__()

    def update(self):
        """
        将同花顺概念股的信息更新至数据库
        """
        #第一层 更新概念时间表 接口: stock_board_concept_name_ths
        self.update_stock_board_concept_name_ths()
        print(ak.stock_board_concept_name_ths())
        #第二层 更新概念股票列表 接口: stock_board_concept_cons_ths
        print(ak.stock_board_concept_cons_ths())
        #第三层 更新概念股票信息 接口: stock_board_concept_detail_ths
        print(ak.stock_board_concept_detail_ths())
        #第四层 更新概念股票历史信息 接口: stock_board_concept_detail_hist_ths
        print(ak.stock_board_concept_detail_hist_ths())

    def update_stock_board_concept_name_ths(self):
        """
        更新同花顺概念时间表
        目标地址: http://q.10jqka.com.cn/gn/detail/code/301558/
        描述: 同花顺-板块-概念板块-概念
        限量: 单次返回当前所有概念时间表；日期为空的为补充概念
        列表名          名称	类型	描述
        date            日期	object	-
        concept_name    概念名称	object	-
        count           成分股数量	int64	-
        url             网址	object	-
        ths_code        代码	object	同花顺内部代码
        """
        df = ak.stock_board_concept_name_ths()
        df_db = pd.read_sql('select * from stock_board_concept_name_ths',con = self.engine)
        #更改列名
        df_db.rename(columns={"日期":"date" , "概念名称":"concept_name" , "成分股数量":"count" , "网址":"url" , "代码":"ths_code" } , errors="raise" , inplace = True)
        #差集更新
        df_diff = pd.concat([df,df_db]).drop_duplicates(keep=False)
        #更新数据库
        df_diff.to_sql(
                name = 'stock_board_concept_name_ths',
                con = ak_data.engine,
                index = False,
                if_exists = 'append')            
    def __update_stock_board_concept_cons_ths(self):
        pass

if __name__ == '__main__':
    a = pro_api()
    th = ths()
    ak_data = ak_data()
    a.start_date = datetime(2023,3,1,8)
    a.end_date = datetime(2023,3,20,16)
    a.code = '159949.SZ'
    a.ktype = '1d'
    
    th.function_A()
    th.update()
    #df = a.stock_basic()
    #获取同花顺某个板块的全部个股
    df = ak.stock_board_concept_cons_ths(symbol="PEEK材料")
    #将df中的代码列中的代码转换为akshare的代码
    df['代码'] =df['代码'].apply(lambda x: ak_data.code_ak_to_ts(x))
    #df['代码'].apply(lambda x: ak_data.code_ak_to_ts(a,x))
    print(df)
    df = a.ths.update()
    print(df)
    pd.set_option('display.max_rows', None)  # Set display option to show all rows

    