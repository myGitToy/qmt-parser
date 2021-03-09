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
"""
【模型说明】
采用超过分位数0.6买入，低于分位数0.4卖出的简单策略
本模型采用单买单卖策略，全仓买入或卖出









"""
class TestStrategy(bt.Strategy):
    params=(('high_period',14),     #最高价（使用的是收盘价的最高价）向前回滚的时间周期 
            ('atr_period',14),      #ATR向前回滚的时间周期 
            ('min_ticksize',3),     #最小的价格单位 通常ETF为小数点后3位，一般证券为2位
            ('prank_period',14),    #分位数向前回滚的时间周期  
            ('printlog',True),)     #是否打印 默认是
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

        #self.np75 = np.percentile(self.datas[0].close, 75)
        self.prank = bt.ind.PctRank(period= self.params.prank_period , plot = True ,subplot=True)
        self.sma5 = bt.indicators.SimpleMovingAverage(self.datas[0].close, period = 30)  #这里用self.datas[0].close 或者self.dataclose 或者self.data.close(0)都可以
        #self.x = bt.indicators.Highest()
        #增强型图表不支持self.data.close(0) 的格式
        #self.sma10 = bt.indicators.SimpleMovingAverage(self.data.close(0) , period = 10)
        #self.sma30 = bt.indicators.SimpleMovingAverage(self.data.close(0) , period = 30)
        
        #self.H_line = bt.indicators.Highest(self.datas[0].close , period=50)
        self.high_cut = bt.indicators.Highest(self.datas[0].close * 0.92 , period = self.params.high_period, plot = True , subplot= False) 
        
        #LinePlotterIndicator(self.new_high, name='NEW HIGH')
        self.atr = bt.indicators.AverageTrueRange(self.datas[0] , period = self.params.atr_period )
        self.tr = bt.indicators.TrueRange(self.datas[0])
        #self.tr =  bt.indicators.TrueRange(self.datas[0] )
        #副图叠加ATR指标并作图（增强型图表无法进行叠加）
        #bt.indicators.ATR(self.datas[0] , plot=False , period = 56)
        #bt.indicators.atr(self.datas[0] , period = self.params.maperiod ).plot = True
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

    def next(self):
        # Simply log the closing price of the series from the reference
        #self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.prank > 0.75 and self.dataclose > self.high_cut[0]:
                #全仓买入
                size = int(self.broker.getcash() *0.98 / self.datas[0].close /100) *100
                #结合ATR系统
                #size = int(self.broker.getcash() *0.0025 / self.atr[0] /100 ) *100
                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('买入价, %.3f 买入单位 %.1f'  % (self.dataclose[0] ,size))
                self.log("买入当日ATR值 %.3f" % self.atr[0])
                self.log("当日TR值 %.3f" %self.tr[0])
                
                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy(size=size)

        else:

            if self.dataclose < self.high_cut[0]:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.3f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.close()
    def stop(self):
        self.log("最大回撤:-%.2f%%" % self.stats.drawdown.maxdrawdown[-1])

def get_k_data():
        engine = sqlalchemy.create_engine('mysql+pymysql://stock_user:a@1#Yy1c@localhost:3306/stock')
        query = "select date as datatime,open,high,low,close,volume from jqdata_1d where code = '159949.XSHE' and DATE(date) between '2010-1-1' and '2020-07-16'"    
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
    #print(dataframe)
    data = bt.feeds.PandasData(dataname=dataframe)
    #data.resample()
    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(1000000.0)
    cerebro.broker.setcommission(commission=0.00025)
    # 添加回撤观察器
    cerebro.addobserver(bt.observers.DrawDown)
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
