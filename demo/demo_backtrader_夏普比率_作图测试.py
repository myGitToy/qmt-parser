"""
测试目的：
作图，画出成交价格中位数-2ATR的图表
"""


from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
#导入analyzers
import backtrader.analyzers as btanalyzers

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
测试bt的订单管理：下单 撤单 更改价格等

买点逻辑：100小时分位数大于0.75 执行市价的买入订单
追加逻辑：买入订单成立后，按照每1/2ATR 追加1/2unit计算
卖出逻辑：小于100小时最高价 - 3ATR 清仓


"""
class TestStrategy(bt.Strategy):
    params=(('high_period',25),     #最高价的计算周期（日线默认25 小时线默认100）
            ('atr_period',25),      #ATR的计算周期（日线默认14）
            ('prank_period',25),    #分位数的计算周期（日线默认25 小时线默认100）
            ('R',0.25),             #风险值R设定
            ('atr_size',0.5),         #ATR间隔 默认1个ATR间隔下订单
            ('unit_size',0.5),        #头寸大小 默认每次下单进行1个头寸
            ('open_separation',5),#清仓以后的再次开仓间隔（用来控制反复止损的参数）
            ('printlog',True),)     #是否输出日志 默认True
    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.orefs = list()         #订单列表
        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.last_price = None      #最后的买入价格，用来计算后续每个挡位的买入价格
        # 记录以往订单，在再平衡日要全部取消未成交的订单
        #self.order_list = []
        self.prank = bt.ind.PctRank(period = self.p.prank_period , plot = True ,subplot=True)
        
        #设置ATR指标
        self.atr = bt.indicators.AverageTrueRange(self.datas[0] , period = self.params.atr_period , plot =True , subplot= True , movav = bt.ind.MovAv.EMA)
        #设置头寸指标
        self.unit = self.cerebro.broker.getvalue() * self.params.R /100  / self.atr

        #设置叠加图表 中位数-2ATR
        self.chart2 = self.prank - 2 *self.atr

        
        #设置止损指标
        self.high_cut = bt.indicators.Highest(self.datas[0].close - self.atr * 3 , period = self.params.high_period , plot = True , subplot= False) 
        #副图叠加ATR指标并作图（增强型图表无法进行叠加）
        #bt.indicators.ATR(self.datas[0] , plot=False , period = 25)
    def notify_order(self, order):
        if order.status in [order.Submitted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do , 
            self.log(f"订单已接受并提交，订单号：{order.ref}；提交价格：{order.price}；提交数量：{order.size}"   )
            
            return
        if order.status in [order.Accepted]:
            #交易所已接受订单
            pass         
        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.3f, Cost: %.3f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))
                self.last_price = order.executed.price
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                #输出订单信息,并从有效订单中删除该笔订单
                
                self.log(f"当前执行的订单号：{order.ref}；提交价格：{order.price}；提交数量：{order.size}")
                self.orefs.remove(order)
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.3f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

                self.bar_executed = len(self)
                #关闭最后买入价格，逻辑清零
                #self.last_price = None

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None
    # 交易状态通知，一买一卖算交易
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('交易利润, 毛利润 %.2f, 净利润 %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def get_quantile(self):
        #获取指定周期的分位数信息
        s = pd.Series()
        for num in range(0 , self.params.high_period):
            s.append(self.dataclose[-num])
            


    def next(self):
        #设置头寸
        
        #self.half_unit = int(self.unit[0] / 2 / 100) *100
        #self.unit = int(self.unit[0] /  100) *100
        #self.log(f"bar的头寸为{self.unit[0]}" )
        pos = self.getposition(self.data)
        if pos.size > 0:
            #有头寸，输出头寸值
            self.log(f"仓位:{pos.size} 头寸：{(pos.size/self.unit[0]):.1f}当前价格：{pos.adjbase}")
            #取消未完成的订单
            for o in self.orefs:
                self.log(f"剩余有效订单：订单号：{o.ref}；提交价格：{o.price}；提交数量：{o.size}")
                #self.broker.cancel(o)
                #self.order
                #pass
            #新增订单
            #self.add_long(base_price = self.last_price)
        #self.log(self.unit)
        """
        #单仓位的写法
        for i in enumerate(self.datas):

            pos = self.getposition(i)
            if len(pos):
                self.log(f"买入价 {pos.price}" )
        """
        '''
        #多仓位的写法
        #for i, d in enumerate(self.datas):
            #pos = self.getposition(d)
            #if len(pos):
                #self.log('{}, 持仓:{}, 成本价:{}, 当前价:{}, 盈亏:{:.2f}'.format(
                    #d._name, pos.size, pos.price, pos.adjbase, pos.size * (pos.adjbase - pos.price)))
        '''
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        #检测是否有未完成订单
        if self.order: 
            #无效的
            #self.log(f"pending，订单号：{order.ref}；提交价格：{order.price}；提交数量：{order.size}"   )
            
            return

        # Check if we are in the market
        if not self.position:
            #初始阶段进行下单，挂一个高价格，无法成交的
            #self.order = self.buy(size=100, exectype = bt.Order.StopLimit   )


            # Not yet ... we MIGHT BUY if ...
            if self.prank > 0.75 and self.datas[0].close > self.high_cut[0] :
                size = int(self.unit[0] * self.params.unit_size /100) *100
                #创建买入订单（使用unit动态头寸参数）
                
                p1 = self.dataclose[0]
                
                #p2 = self.dataclose[0] + self.atr[0] * self.params.atr_size
                #p3 = self.dataclose[0] + self.atr[0] * self.params.atr_size * 2
                o1 = self.buy(exectype = bt.Order.Market , size = size ,price = p1)
                #o2 = self.buy(exectype = bt.Order.StopLimit , size = size , price = p2)
                #o3 = self.buy(exectype = bt.Order.StopLimit , size = size , price = p3)
                self.order = o1
                #self.order = o2
                #self.order = o3
                #self.log(f"订单已创建, 订单号：{o1.ref} ；bar收盘价：{self.dataclose[0]:.3f}；数量{o1.size}")
                #self.log(f"订单已创建, 订单号：{o2.ref} ；bar收盘价：{self.dataclose[0]:.3f}；数量{o2.size}")
                #self.log(f"订单已创建, 订单号：{o3.ref} ；bar收盘价：{self.dataclose[0]:.3f}；数量{o3.size}")
                self.orefs.append(o1)
                #self.orefs.append(o2)
                #self.orefs.append(o3)
                self.last_price = p1
                self.add_long(base_price = self.last_price)
                # Keep track of the created order to avoid a 2nd order
                #exectype=bt.Order.StopLimit , price = self.dataclose[0]
                #self.order = self.buy(size=size ,    )

        else:
            #有订单，进行价格下一个bar的价格调整
            self.order
            if self.dataclose[0] < self.high_cut[0]:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.3f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.close()
                #清仓后清除有效订单列表
                for o1 in self.orefs:
                    self.log(f"清仓，删除剩余订单号：{o1.ref}；提交价格：{o1.price}；提交数量：{o1.size}")
                    self.broker.cancel(o1)
                self.orefs = []    

    def add_long(self , base_price = None , base_atr = None , base_unit = None):
        """
        根据ATR结果进行追加订单
        """
        if base_atr == None:
            base_atr = self.atr[0] * self.params.atr_size
        if base_unit == None:
            base_unit = int(self.unit[0] * self.params.unit_size /100) *100
        #创建买入订单（使用unit动态头寸参数）
        if base_price == None:
            return 
        lst = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30]
        for n in lst:
            #创建订单
            p = base_price + base_atr * n
            o = self.buy(exectype = bt.Order.StopLimit , size = base_unit ,price = p)
            self.order = o
            self.orefs.append(o)
        '''
        p1 = base_price + base_atr                
        p2 = base_price + base_atr * 2
        p3 = base_price + base_atr * 3
        o1 = self.buy(exectype = bt.Order.StopLimit , size = base_unit ,price = p1)
        o2 = self.buy(exectype = bt.Order.StopLimit , size = base_unit , price = p2)
        o3 = self.buy(exectype = bt.Order.StopLimit , size = base_unit , price = p3)
        self.order = o1
        self.order = o2
        self.order = o3
        
        #self.log(f"订单已创建, 订单号：{o1.ref} ；bar收盘价：{self.dataclose[0]:.3f}；数量{o1.size}")
        #self.log(f"订单已创建, 订单号：{o2.ref} ；bar收盘价：{self.dataclose[0]:.3f}；数量{o2.size}")
        #self.log(f"订单已创建, 订单号：{o3.ref} ；bar收盘价：{self.dataclose[0]:.3f}；数量{o3.size}")
        self.orefs.append(o1)
        self.orefs.append(o2)
        self.orefs.append(o3)
        '''
if __name__ == '__main__':
    #自定义参数
    code = '300759.XSHE'
    start = datetime.datetime(2020,1,1)
    end = datetime.datetime(2021,8,14)
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
    cerebro.broker.setcash(1000000.0)
    cerebro.broker.setcommission(commission=0.00025)
    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.addanalyzer(bt.analyzers.SharpeRatio,_name = 'SharpeRatio')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='DW')
    # Run over everything
    #cerebro.run()
    #cerebro.plot()

    #增加Analyzers模块
    cerebro.addanalyzer(btanalyzers.SharpeRatio_A, _name='mysharpe')
    thestrats = cerebro.run()
    
    thestrat = thestrats[0]
    print('夏普比率:', thestrat.analyzers.mysharpe.get_analysis())

    cerebro.plot()

    #使用增强型图形输出
    #b = Bokeh(style="bar", tabs="multi", scheme=Tradimo())
    #cerebro.plot(b)
    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
