from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import backtrader as bt
import backtrader.feeds as btfeeds
import sqlalchemy
import pandas as pd
#from demo_backtrader_getdata_pandas import get_k_data

def get_k_data():
        engine = sqlalchemy.create_engine('mysql+pymysql://stock_user:a@1#Yy1c@localhost:3306/stock')
        query = "select date as datatime,open,high,low,close,volume from jqdata_1d where code = '159949.XSHE' and DATE(date) between '2021-1-1' and '2021-02-21'"    
        df_db = pd.read_sql_query(query , engine)
        if df_db.empty == True:
            #无数据
            print("无数据")
            return pd.dataframe()
        else:
            #有数据
            df_db['openinterest'] = 0
            df_db['datatime'] = pd.to_datetime(df_db['datatime'])
            df_db.set_index(["datatime"], inplace=True)
            
            return df_db