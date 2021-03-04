from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
#使用增强型图形输出
from backtrader_plotting import Bokeh
from backtrader_plotting.schemes import Tradimo
import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
import argparse
# Import the backtrader platform
import backtrader as bt
import pandas as pd
import sqlalchemy


# Create a Stratey
class TestStrategy(bt.Strategy):
    params=(('maperiod',14),
            ('printlog',True),)
    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        #self.np75 = np.percentile(self.datas[0].close, 75)
        self.prank = bt.ind.PctRank(period=100)
        self.sma5 = bt.indicators.SimpleMovingAverage(self.datas[0].close, period = 5)  #这里用self.datas[0].close 或者self.dataclose 或者self.data.close(0)都可以
        #增强型图表不支持self.data.close(0) 的格式
        #self.sma10 = bt.indicators.SimpleMovingAverage(self.data.close(0) , period = 10)
        #self.sma30 = bt.indicators.SimpleMovingAverage(self.data.close(0) , period = 30)
        
        self.H_line = bt.indicators.Highest(self.datas[0].close , period=50)
        
        
        #LinePlotterIndicator(self.new_high, name='NEW HIGH')
        #self.atr = bt.indicators.AverageTrueRange(self.datas[0] , period = self.params.maperiod)
        #self.tr =  bt.indicators.TrueRange(self.datas[0] )
        #副图叠加ATR指标并作图（增强型图表无法进行叠加）
        bt.indicators.ATR(self.datas[0], plot=True , period = 25)
        #bt.indicators.atr(self.datas[0] , period = self.params.maperiod ).plot = True


    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])
        #self.new_high = self.data.close[0] >= self.H_line[0]
        #print(self.new_high[0].value)
        #self.log('Close, %.2f' % self.H_line )

        #self.log('Close, %.2f' % self.datas[0].close)
        #self.log('Close, %.2f' % self.sma[0])
        if self.dataclose[0] < self.dataclose[-1]:
        #if self.datas[0].close <  self.datas[-1].close:
            # current close less than previous close

            if self.dataclose[-1] < self.dataclose[-2]:
            #if self.datas[-1].close <  self.datas[-2].close:
                # previous close less than the previous close

                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                print(f'移动平均线, {self.sma5[0]}')
                #print(f'ATR, {self.atr[0]}')
                #print(f'TR, {self.tr[0]}')
                self.buy()

def get_k_data():
        engine = sqlalchemy.create_engine('mysql+pymysql://stock_user:a@1#Yy1c@localhost:3306/stock')
        query = "select date as datatime,open,high,low,close,volume from jqdata_60m where code = '512290.XSHG' and DATE(date) between '2019-10-1' and '2021-02-21'"    
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

if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(TestStrategy)

    # Create a Data Feed
    dataframe =  get_k_data()
    print(dataframe)
    data = bt.feeds.PandasData(dataname=dataframe)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.addanalyzer(bt.analyzers.SharpeRatio,_name = 'SharpeRatio')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='DW')
    # Run over everything
    cerebro.run()
    cerebro.plot()
    #使用增强型图形输出
    #b = Bokeh(style="bar", tabs="multi", scheme=Tradimo())
    #cerebro.plot(b)
    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
