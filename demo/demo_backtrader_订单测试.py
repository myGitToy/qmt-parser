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
import numpy as np
from apt.vendor.jqdata.base import base
from apt.vendor.jqdata.jqdata import data as jqdata

# Create a Stratey
"""
【模型说明】
采用超过分位数0.6买入，低于分位数0.4卖出的简单策略









"""
class TestStrategy(bt.Strategy):
    params=(('high_period',100),
            ('atr_period',14),
            ('prank_period',14),
            ('printlog',True),)
    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.prank = bt.ind.PctRank(period=self.p.prank_period , plot = True ,subplot=True)
        self.high_cut = bt.indicators.Highest(self.datas[0].close *0.85 , period=100 , plot = True , subplot= False) 
        #副图叠加ATR指标并作图（增强型图表无法进行叠加）
        bt.indicators.ATR(self.datas[0] , plot=False , period = 25)
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.3f, Cost: %.3f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.3f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def get_quantile(self):
        #获取指定周期的分位数信息
        s = pd.Series()
        for num in range(0 , self.params.high_period):
            s.append(self.dataclose[-num])
            


    def next(self):
        # Simply log the closing price of the series from the reference
        #self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:  
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.prank > 0.75:
                size = int(self.broker.getcash() *0.95 / self.datas[0].close /100) *100
                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.3f' % self.dataclose[0])
                
                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy(size=size , exectype=bt.Order.StopLimit , price = self.dataclose[0]  )

        else:

            if self.prank < 0.40:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.3f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.close()


def get_k_data():
        engine = sqlalchemy.create_engine('mysql+pymysql://stock_user:a@1#Yy1c@localhost:3306/stock')
        query = "select date as datatime,open,high,low,close,volume from jqdata_60m where code = '512290.XSHG' and DATE(date) between '2019-10-1' and '2021-04-21'"    
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
    #自定义参数
    code = '601318.XSHG'
    start = datetime.datetime(2016,12,1)
    end = datetime.datetime(2021,3,11)
    ktype = '1d'
    d = jqdata(rds_host = jqdata.数据源.localhost , myauth= False)
    df_db = d.get_k_data(code = code  , start_date = start , end_date = end, ktype = ktype , fq = d.复权.前复权)
    #数据做适配
    df_db['openinterest'] = 0
    df_db['datatime'] = pd.to_datetime(df_db['date'])
    df_db.set_index(["datatime"], inplace=True)
    print(df_db)
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(TestStrategy)

    # Create a Data Feed
    data = bt.feeds.PandasData(dataname = df_db)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.00025)
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
