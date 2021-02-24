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
        query = "select date as datatime,open,high,low,close,volume from jqdata_60m where code = '515030.XSHG' and DATE(date) between '2020-12-1' and '2021-02-21'"    
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

def runstrat():
    args = parse_args()

    # Create a cerebro entity
    cerebro = bt.Cerebro(stdstats=False)

    # Add a strategy
    cerebro.addstrategy(bt.Strategy)

    # Get a pandas dataframe
    datapath = ('../../datas/2006-day-001.txt')

    # Simulate the header row isn't there if noheaders requested
    skiprows = 1 if args.noheaders else 0
    header = None if args.noheaders else 0

    #dataframe = pandas.read_csv(datapath,skiprows=skiprows,header=header,parse_dates=True,index_col=0)

    dataframe =  get_k_data()
    print(dataframe)

    if not args.noprint:
        print('--------------------------------------------------')
        print(dataframe)
        print('--------------------------------------------------')

    # Pass it to the backtrader datafeed and add it to the cerebro
    data = bt.feeds.PandasData(dataname=dataframe)

    cerebro.adddata(data)

    # Run over everything
    cerebro.run()

    # Plot the result
    cerebro.plot(style='bar')


def parse_args():
    parser = argparse.ArgumentParser(
        description='Pandas test script')

    parser.add_argument('--noheaders', action='store_true', default=False,
                        required=False,
                        help='Do not use header rows')

    parser.add_argument('--noprint', action='store_true', default=False,
                        help='Print the dataframe')

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
