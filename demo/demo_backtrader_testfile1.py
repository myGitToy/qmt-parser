from __future__ import (absolute_import, division, print_function, unicode_literals)
import datetime  
import os.path  
import sys  
import backtrader as bt
import tushare as ts
import argparse
import pandas as pd
import sqlalchemy

class TestStrategy(bt.Strategy):    
    params = (        
        ('maperiod', 15),
        ('printlog', False),
    )    

    def log(self, txt, dt=None, doprint=False): 
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.sma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.maperiod) 
        #添加ATR
        #self.atr = bt.indicators.
        self.dataclose = self.datas[0].close

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:                          
            return       
        if order.status in [order.Completed]:           
            if order.isbuy():
                self.log('BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f '%
                        (order.executed.price,
                        order.executed.value,
                        order.executed.comm))                

                self.buyprice = order.executed.price                
                self.buycomm = order.executed.comm
            else:              
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %                         
                        (order.executed.price,                          
                        order.executed.value,                          
                        order.executed.comm)) 

                self.bar_executed = len(self)
        #elif order.status in [order.Canceled, order.Margin, order.Rejected]:            
            #self.log('Order Canceled/Margin/Rejected')        
            #self.order = None    

        def notify_trade(self, trade):
            if not trade.isclosed:
                return        
            self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %                
                      (trade.pnl, trade.pnlcomm))    

    def next(self): 
            self.log('Close, %.2f' % self.dataclose[0])       
            if self.order:           
                return        
            # 简单策略，当日收盘价大于简单滑动平均值买入，当日收盘价小于简单滑动平均值卖出
            if not self.position:           
                if self.dataclose[0] > self.sma[0]:            
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])             
                    self.order = self.buy()       
            else:
                if self.dataclose[0] < self.sma[0]:              
                    self.log('SELL CREATE, %.2f' % self.dataclose[0])              
                    self.order = self.sell()   
    def stop(self):       
            self.log('(MA Period %2d) Ending Value %.2f' %
            (self.params.maperiod, self.broker.getvalue()), doprint=True)
def get_k_data():
        engine = sqlalchemy.create_engine('mysql+pymysql://stock_user:a@1#Yy1c@localhost:3306/stock')
        query = "select date as datatime,open,high,low,close,volume from jqdata_1d where code = '159949.XSHE' and DATE(date) between '2020-1-1' and '2021-02-21'"    
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
        #创建主控制器
        cerebro = bt.Cerebro()      
        #导入策略参数寻优(10-30之间输出最佳的结果)
        cerebro.optstrategy(TestStrategy,maperiod=range(10, 31))    
        #准备股票日线数据，输入到backtrader
        datapath = ('C:/testbacktrader/tushare/300274.csv')                      
        dataframe =  get_k_data()   
        print(dataframe)
        data = bt.feeds.PandasData(dataname=dataframe)
  
        cerebro.adddata(data)
        #broker设置资金、手续费
        cerebro.broker.setcash(100000.0)           
        cerebro.broker.setcommission(commission=0.001)    
        #设置买入设置，策略，数量
        cerebro.addsizer(bt.sizers.FixedSize, stake=100000)   
        print('Starting Portfolio Value: %.2f' %                    
        cerebro.broker.getvalue())    
        cerebro.run(maxcpus=1)    
        print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())  
        cerebro.plot()
