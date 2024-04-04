from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
#导入analyzers
import backtrader.analyzers as btanalyzers

#使用增强型图形输出
from backtrader_plotting import Bokeh
from backtrader_plotting.schemes import Tradimo

from datetime import datetime # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
import argparse
# Import the backtrader platform
import backtrader as bt
import pandas as pd
import sqlalchemy
import numpy as np
from apt.vendor.akshare.data import data as ak_data

# Create a Stratey
"""
【模型说明】
测试bt的订单管理：下单 撤单 更改价格等

买点逻辑：100小时分位数大于0.75 执行市价的买入订单
追加逻辑：买入订单成立后，按照每1/2ATR 追加1/2unit计算
卖出逻辑：小于100小时最高价 - 2ATR 清仓


"""
class TestStrategy(bt.Strategy):
    params=(('high_period',25),     #最高价的计算周期（日线默认25 小时线默认100）
            ('atr_period',25),      #ATR的计算周期（日线默认14）
            ('prank_period',45),    #短周期分位数的计算周期（日线默认25 小时线默认100）
        #长周期仓位控制
            ('prank_long_period',60),    #长周期分位数的计算周期（默认半年线120）
            ('R',0.25),             #风险值R设定
            ('atr_size',0.5),         #ATR间隔 默认1个ATR间隔下订单
            ('atr_cut',2),            #从最止损的ATR
            ('unit_size',0.5),        #头寸大小 默认每次下单进行1个头寸
            ('open_separation',5),#清仓以后的再次开仓间隔（用来控制反复止损的参数）
            ('printlog',False),     #是否输出日志 默认True
        #布林线控制指标
            ('boll_period',20),     #布林线周期
            ('boll_devfactor',2),         #布林线标准差
            ('boll_atr',1),         #布林线ATR间隔
            ('volume_factor', 1.5),  # 布林线上轨放量因子
            ('volume_period', 20),  # 成交量计算周期
            ('boll_size',0.5),)      #布林线头寸大小

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0) 
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        #增加指标indicators
        BollingerBandsVolume(self.data)
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.dataopen = self.datas[0].open
        self.orefs = list()         #订单列表
        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.last_price = None      #最后的买入价格，用来计算后续每个挡位的买入价格
        # 记录以往订单，在再平衡日要全部取消未成交的订单
        #self.order_list = []
        #self.prank = bt.ind.PctRank(period = self.p.prank_period , plot = True ,subplot=True)
        self.prank = bt.indicators.PercentRank(self.datas[0].close, period = self.p.prank_period , plot = False , subplot = True )
        self.long_prank = bt.indicators.PercentRank(self.datas[0].close, period = self.p.prank_long_period , plot = True , subplot = True )
        #self.whiteSoldier = bt.talib.talib.CDL3WHITESOLDIERS(self.data.open,self.data.high,self.data.low,self.data.close )
        self.cdl = bt.talib.CDL3INSIDE(self.data.open, self.data.high, self.data.low, self.data.close)
        #设置均线多头排列
        #self.ma_crossover = MA_CrossOver(self.datas[0] , fast = 5 , slow = 10 , very_slow = 20 , plot = True , subplot = True)
        self.ma_crossover = EMA_CrossOver(self.datas[0])
        #self.macd = bt.indicators.MACD(self.data , plot = True , subplot = True )
        #设置ATR指标
        self.atr = bt.indicators.AverageTrueRange(self.datas[0] , period = self.params.atr_period , plot = True , subplot= True , movav = bt.ind.MovAv.EMA)
        #设置头寸指标
        self.unit = self.cerebro.broker.getvalue() * self.params.R /100  / self.atr        
        #设置止损指标
        self.high_cut = bt.indicators.Highest(self.datas[0].close - self.atr * self.params.atr_cut , period = self.params.high_period , plot = True , subplot= False) 
        #副图叠加ATR指标并作图（增强型图表无法进行叠加）
        #bt.indicators.ATR(self.datas[0] , plot= False , period = 25) #这条这条有作用，但是不如self.atr = bt.indicators.AverageTrueRange ，且无法设置EMA类型
        # 添加布林线指标
        self.boll = bt.indicators.BollingerBands(self.data.close, period = self.params.boll_period, devfactor=self.params.boll_devfactor)
        # 计算成交量的均线
        self.volume_sma = bt.indicators.SimpleMovingAverage(self.data.volume, period=self.params.volume_period)
        # 添加布林线上轨放量指标
        self.bb_volume = self.data.volume * (self.data.close > self.boll.lines.top) * (self.data.volume > self.volume_sma * self.params.volume_factor)
        # 在副图中绘制布林线上轨放量指标
        #self.bb_volume.plotinfo.subplot = True

    def notify_order(self, order):
        if order.status in [order.Submitted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do , 
            self.log(f"订单已接受并提交，订单号：{order.ref}；提交价格：{order.price}；提交数量：{order.size}"   )
            
            return
        if order.status in [order.Accepted]:
            #交易所已接受订单
            #打印目前现有订单
            self.log(f"交易所现存订单有：")
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
            
    def stop(self):
        self.log("最大回撤:-%.2f%%" % self.stats.drawdown.maxdrawdown[-1])

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
            #self.order = self.buy(size=100, exectype = bt.Order.StopLimit)


            # Not yet ... we MIGHT BUY if ...
            #建仓的条件：1.价格大于100小时分位数的0.75 2.价格大于100小时最高价 - 2ATR 3. 均线多头排列
            if self.prank > 0.75 and self.datas[0].close > self.high_cut[0] and self.ma_crossover.lines.ema_crossover[0] == 1:
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
class BollingerBandsVolume(bt.Indicator):
    lines = ('bb_volume', 'top', 'mid', 'bot', 'width','is_narrowing')
    params = (('period', 20), ('devfactor', 2.0), ('volume_factor', 1.5),)
    plotinfo = dict(subplot=True)  # 在副图中显示指标
    plotlines = dict(
        is_narrowing=dict(_plotskip=False),  # 在副图中显示 is_narrowing
    )    
    def __init__(self):
        # 添加布林线指标
        self.boll = bt.indicators.BollingerBands(self.data.close, period=self.params.period, devfactor=self.params.devfactor)
        # 获取布林线的上轨线、中轨线和下轨线
        self.lines.top = self.boll.lines.top
        self.lines.mid = self.boll.lines.mid
        self.lines.bot = self.boll.lines.bot
        # 计算布林线通道宽度
        self.lines.width = self.boll.lines.top - self.boll.lines.bot
        # 判断布林线是否收口并添加is_narrowing 指标
        self.lines.is_narrowing = bt.If(self.lines.width < self.lines.width(-1), 1.0, 0.0)
        #self.lines.is_narrowing.plotinfo.plot = True
        #self.lines.is_narrowing.plotinfo.plotmaster = self.data
        self.lines.is_narrowing.plotlines = dict(
            is_narrowing=dict(marker='*', markersize=8.0, color='lime', fillstyle='full')
        )
        # 计算成交量的均线
        self.volume_sma = bt.indicators.SimpleMovingAverage(self.data.volume, period=self.params.period)

        # 计算布林线上轨放量
        self.lines.bb_volume = self.data.volume * (self.data.close > self.boll.lines.top) * (self.data.volume > self.volume_sma * self.params.volume_factor)

        # 在副图中绘制布林线上轨放量指标
        #self.plotinfo.subplot = True
class EMA_CrossOver(bt.Indicator):
    lines = ('ema_crossover',)
    params = (('fast', 10), ('slow', 20), ('very_slow', 30))

    def __init__(self):
        ma_fast = bt.indicators.EMA(self.data, period=self.params.fast)
        ma_slow = bt.indicators.EMA(self.data, period=self.params.slow)
        ma_very_slow = bt.indicators.EMA(self.data, period=self.params.very_slow)
        #均线多头排列 ma_fast > ma_slow > ma_very_slow
        #self.lines.ema
        ma_fast_ind = ma_fast > ma_slow
        ma_slow_ind = ma_slow > ma_very_slow
        self.lines.ema_crossover = bt.And(ma_fast > ma_slow , ma_slow > ma_very_slow )

        #self.lines.ema_crossover = bt.And(bt.indicators.CrossOver(ma_fast, ma_slow) , bt.indicators.CrossOver(ma_slow, ma_very_slow) , bt.indicators.CrossOver(ma_fast, ma_very_slow) )

if __name__ == '__main__':    #自定义参数
    data = ak_data()
    data.code = '600072.SH'
    data.start_date = datetime(2022,1,1)
    data.end_date = datetime(2023,12,31)
    data.ktype = '1d'
    df_db = data.get_k_data()
    df_db['openinterest'] = 0
    df_db['datatime'] = pd.to_datetime(df_db['date'])
    df_db.set_index(["datatime"], inplace=True)
    print(df_db)
    # Create a cerebro entity
    #在这里设定是否静默输出（貌似无效）
    cerebro = bt.Cerebro(optreturn=True)

    # Add a strategy
    cerebro.addstrategy(TestStrategy)
    #增加最大回撤观察窗口
    cerebro.addobserver(bt.observers.DrawDown)
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
    cerebro.addanalyzer(btanalyzers.DrawDown, _name='mydrawdown')
    thestrats = cerebro.run()
    
    thestrat = thestrats[0]
    print('夏普比率:', thestrat.analyzers.mysharpe.get_analysis())
    print('最打回撤' , thestrat.analyzers.mydrawdown.get_analysis())
    print(thestrat.analyzers.mydrawdown.get_analysis()['max']['drawdown'])
    cerebro.plot()

    #使用增强型图形输出
    #b = Bokeh(style="bar", tabs="multi", scheme=Tradimo())
    #cerebro.plot(b)
    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
