"""
此模型对于海龟模型原版的改良之处有：
1. 卖出采用触发ATR-X之后开始计算低于此价格的天数，大于N天就执行清仓，与第二天开盘卖出

"""
import backtrader as bt # 导入 Backtrader
import backtrader.indicators as btind # 导入策略分析模块
import backtrader.feeds as btfeeds # 导入数据模块
import pandas as pd
import sqlalchemy
import numpy as np
from datetime import datetime
from bt.Data import Data as Data #导入bt本地数据模块
from apt.vendor.jqdata.base import base #导入jqta base模块
from apt.vendor.jqdata.jqdata import data as jqdata #导入jqta jqdata模块
from bt.Data import CustomData_PEPB as pe
from datetime import timedelta

class PandasData_more(bt.feeds.PandasData):
    lines = ('pe', 'pb', ) # 要添加的线
    # 设置 line 在数据源上的列位置
    params=(
        ('pe', -1),
        ('pb', -1),
           )
    # -1表示自动按列明匹配数据，也可以设置为线在数据源中列的位置索引 (('pe',6),('pb',7),)

# 创建策略
class TestStrategy(bt.Strategy):
    # 可选，设置回测的可变参数：如移动均线的周期
    params=(('max_unit',6),        #最大交易头寸
            ('high_period',25),     #最高价的计算周期（日线默认25 小时线默认100）
            ('atr_period',25),      #ATR的计算周期（日线默认14）
            ('prank_period',25),    #分位数的计算周期（日线默认25 小时线默认100）
            ('R',0.25),             #风险值R设定
            ('atr_size',1),         #ATR间隔 默认1个ATR间隔下订单
            ('unit_size',1),        #头寸大小 默认每次下单进行1个头寸
            ('cut_atr',2),          #从最高点收盘价下跌N个ATR则进行清仓
            ('open_separation',5),#清仓以后的再次开仓间隔（用来控制反复止损的参数）
            ('printlog',False),)     #是否输出日志 默认True
    def log(self, txt, dt=None):
        '''可选，构建策略打印日志的函数：可用于打印订单记录或交易记录等'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        '''必选，初始化属性、计算指标等'''
        #########记录海龟模型的状态变量#############
        #设置上一次买入的价格
        self.last_price = None
        #初始买入点
        self.init_price = None
        # 用于记录订单状态
        self.order = None
        #记录理论头寸
        self.t_unit = None
        #设置prank指标
        #self.prank = bt.indicators.PercentRank(self.datas[0].close, period = self.p.prank_period , plot = True , subplot = True )
        #设置ATR指标
        self.atr = bt.indicators.AverageTrueRange(self.datas[0] , period = self.params.atr_period , plot = True , subplot= True , movav = bt.ind.MovAv.EMA)
        #设置头寸指标
        self.unit = self.cerebro.broker.getvalue() * self.params.R /100  / self.atr 
        #设置止损指标
        self.high_cut = bt.indicators.Highest(self.datas[0].close - self.atr * self.params.cut_atr , period = self.params.high_period , plot = True , subplot= False) 
        #设置EMA均线
        self.ema_short = bt.talib.EMA(self.datas[0], timeperiod = 14)
        self.ema_long = bt.talib.EMA(self.datas[0], timeperiod = 120)
        #设置交易信号
        self.singal_below_cut = bt.Cmp(self.high_cut , self.datas[0].close)   #用于处理收盘价是否高于止损价的信号
        self.singal_pos_close = 0        #用于处理是否进行止损操作的信号
        #self.test_singal = SellAllInd()
        self.signal_abv_ema_long = bt.And(self.datas[0] > self.ema_long)
        self.signal_sell = bt.And(self.datas[0].close < self.high_cut)
        #####设置EMA均线SLOPE指标

        #talib技术指标
        self.doji = bt.talib.CDL3STARSINSOUTH(self.data.open, self.data.high,self.data.low, self.data.close)       
        #self.ema = bt.talib.EMA(self.datas[0].close , timeperiod = 5)
        #self.ema = bt.talib.talib.EMA(self.datas[0].close)

    def notify_order(self, order):
        '''可选，打印订单信息'''
        if order.status in [order.Submitted]:
            #cerebro已提交订单
            #self.log(f"订单已提交，订单号：{order.ref}；提交价格：{order.price}；提交数量：{order.size}；订单状态：{order.Status[order.status]}"   )
            pass

        if order.status in [order.Accepted]:
            #交易所已接受订单
            #打印目前现有订单
            """
            self.log(f"#########交易所接收到新订单，现存有效订单有：#######")
            for o in self.broker.get_orders_open():
                self.log(f"订单编号{o.ref}；订单价格{o.price:.3f}；订单数量{o.size};")
            """    
        if order.status in [order.Completed]:
            if order.isbuy():
                #self.log('BUY EXECUTED, Price: %.3f, Cost: %.3f, Comm %.2f' % (,order.executed.value,order.executed.comm))
                self.last_price = order.executed.price
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                '''
                #输出订单信息,并从有效订单中删除该笔订单
                self.log("##################################################################")
                self.log(f"###有订单成交，订单编号：{order.ref}###")
                self.log(f"###成交价格：{order.executed.price}；成交数量：{order.size};税费：{order.executed.comm:.2f}###")   
                self.log("##################################################################")

                #交易已完成，执行新的止损单
                for o in self.broker.get_orders_open():
                    if o.ordtype == 1:
                        #由于有新的买入单子，所以原有的止损单数量不对了，设定新的止损单
                        self.broker.cancel(o)
                #设立新的止损单
                self.order = self.sell(exectype = bt.Order.StopLimit , price = 180 , size = self.getposition(self.data).size )
                '''
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.3f, Cost: %.2f, Comm %.2f' %(order.executed.price,order.executed.value,order.executed.comm))
                pass
                #self.bar_executed = len(self)
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            #订单被交易所取消，判断是否需要重新下单
            pass
            #self.log('****************************************Order Canceled/Margin/Rejected')

        #订单处理完成
        self.order = None

    def notify_trade(self, trade):
        '''可选，打印交易信息'''
        pass

    def next(self):
        '''必选，编写交易策略逻辑'''
        self.log("##########当日委托单#############")
        for o in self.broker.get_orders_open():
            self.log(f"订单编号{o.ref}；订单价格{o.price:.3f}；订单数量{o.size};")
        print(f"{self.datas[0].datetime.date()}:当前持仓量:{self.getposition(self.data).size}；持仓成本{self.getposition(self.data).price}；收盘价{self.datas[0].close[0]:.3f}")
        #print(self.rolling_data[:0])
        sma = btind.SimpleMovingAverage(...) # 计算均线
        #计算清仓指标(清仓标准是收盘价连续2天低于high_cut，则于第三天开盘卖出清仓)
        self.sell_all = self.singal_pos_close[0] + self.singal_pos_close[-1] 
        print(self.sell_all)
        #计算百分比)
        
        ######获取仓位情况
        pos = self.getposition(self.data)
        if pos.size == 0 :
            #未开仓状态，下面有两种可能性：
            #1. 未开仓 未挂单：新建挂单
            #2. 未开仓 有挂单：修改挂单
            #计算75分位数的买入价格
            self.quantile_value  = np.quantile(self.datas[0].close.get(size = 20), [0.25, 0.5, 0.75 , 0.85], interpolation = 'linear')
            #print(f"当前P75值为：{self.quantile_value[1]}")
            #买入价格的基准线是75分位数和EMA120均线取高者
            base_price = round(max(self.quantile_value[2] , self.ema_long[0]) , 3)
            if len(self.broker.get_orders_open()) == 0:
                #对应上面情况1
                #挂单2个头寸
                self.order = self.buy(exectype = bt.Order.StopLimit , price = base_price ,  size = int(self.unit[0] /100) * 100 )
                self.order = self.buy(exectype = bt.Order.StopLimit , price = base_price + self.atr[0] ,  size = int(self.unit[0] /100) * 100 )
            else:
                #对应上面的情况2
                #删除挂单并下2个订单
                for o in self.broker.get_orders_open():
                    self.broker.cancel(o)
                self.order = self.buy(exectype = bt.Order.StopLimit , price = base_price , size = int(self.unit[0] /100) * 100 )
                self.order = self.buy(exectype = bt.Order.StopLimit , price = base_price + self.atr[0] ,  size = int(self.unit[0] /100) * 100 )
            #持仓为0 且交易所订单列表为0，则进入
            #print(f"{self.datas[0].datetime.date():}无订单正在处理")3

        else:
            #######有开仓的仓位
            ###修改委托单
            for o in self.broker.get_orders_open():
                self.broker.cancel(o)
            if pos.size <= self.unit[0] * 4.5:
                #当前持仓头寸小于4个，正常添加两个头寸
                self.order = self.buy(exectype = bt.Order.StopLimit , price = self.last_price , size = int(self.unit[0] /100) * 100 )
                self.order = self.buy(exectype = bt.Order.StopLimit , price = self.last_price + self.atr[0] ,  size = int(self.unit[0] /100) * 100 )
            elif (pos.size > self.unit[0] * 4.5) and (pos.size < self.unit[0] * 6.5):
                #添加一个头寸
                self.order = self.buy(exectype = bt.Order.StopLimit , price = self.last_price + self.atr[0] ,  size = int(self.unit[0] /100) * 100 )


            ###修改止损单
            #止损单计数器，如果有止损单，则置1，如果全部读取完毕仍无止损单，则后续会添加一笔止损
            sell_count = 0 
            for s in self.broker.get_orders_open():

                if s.ordtype == 1:
                    self.broker.cancel(s)
                    self.order = self.sell(exectype = bt.Order.StopLimit , price = round(self.high_cut[0] , 3), size = pos.size )
            if sell_count == 0:
                #委托单中无止损单，主动添加一笔止损单
                self.order = self.sell(exectype = bt.Order.StopLimit , price = round(self.high_cut[0] , 3), size = pos.size )
            ##使用broker来获取订单列表
            for o in self.broker.get_orders_open():
                self.log(f"[Broker]订单编号{o.ref}；订单类型：{o.OrdTypes[o.ordtype]}；订单价格{o.price:.3f}；订单数量{o.size};订单类型{o.Status[o.status]}")

    def stop(self):
        '''策略结束，对应最后一根bar'''
        # 告知系统回测已完成，可以进行策略重置和回测结果整理了
        pass

class SellAllInd(bt.Indicator):
    # 将计算的指标命名为 'dummyline'，后面调用这根 line 的方式有：
    # self.lines.dummyline ↔ self.l.dummyline ↔ self.dummyline
    lines = ('sell_all',)
    # 定义参数，后面调用这个参数的方式有：
    # self.params.xxx ↔ self.p.xxx
    params = (('value', 5),)
    
    def __init__(self):
        """
        __init__() 中是对 line 进行运算，最终也以 line 的形式返回，所以运算结果直接赋值给了 self.l.dummyline；
        """
        self.lines.sell_all = "p"
        #self.lines.sell_all = bt.Max(0.0, self.p.value)
    
    def next(self):
        """
        next() 中是对当前时刻的数据点进行运算（用了常规的 max() 函数），
        返回的运算结果也只是当前时刻的值，所以是将结果赋值给 dummyline 的当前时刻：
        self.l.dummyline[0]， 然后依次在每个 bar 都运算一次；
        """

        self.lines.sell_all[0] = max(0.0, self.p.value)
   
    def once(self, start, end):
        """
        once() 也只运行一次，是更为纯粹的 python 运算，少了 Backtrader 味道，不是直接对指标 line 进行操作，而只是单纯的 python 运算和赋值；
        dummy_array = self.lines.sell_all.array
        for i in xrange(start, end):
            dummy_array[i] = max(0.0, self.p.value)
        """
if __name__ == '__main__':
    # 实例化 cerebro #########
    #不需要调参的实例化
    #cerebro = bt.Cerebro()
    #调参实例化
    #optdatas=True：在处理数据时会采用相对节省时间的方式，进而提高优化速度；
    #optreturn=True：在返回回测结果时，为了节省时间，只返回与参数优化最相关的内容（params 和 analyzers），而不会返回参数优化不关心的数据（比如 datas, indicators, observers …等）；
    cerebro = bt.Cerebro(optdatas=True, optreturn=True)
    ######### 通过 feeds 读取数据 #########
    d = Data()
    d.code = '600036.XSHG'
    d.start = datetime(2021,1,1)
    d.end = datetime(2022,12,10)
    d.ktype = '1d'
    d.myauth = False
    df_db = d.get_bt_data()
    ####标准的数据投喂
    data = bt.feeds.PandasData(dataname = df_db)
    ####自定义数据投喂
    #df_db['pe'] = 2 # 给原先的data1新增pe指标（简单的取值为2）
    #df_db['pb'] = 3 # 给原先的data1新增pb指标（简单的取值为3）
    #p = pe()
    #df_db = p.add_data(code = d.code , df = df_db)
    #data = pe(dataname = df_db)
    #data = PandasData_more(dataname = df_db )
    #测试数据查询功能 
    print(df_db.query("index >= '2021/11/20' & index <='2021/11/29'"))
    # 将数据传递给 “大脑” #########
    cerebro.adddata(data , name = d.code) #自定义数据集的名称（用证券代码）
    ######### 通过经纪商设置初始资金 #########
    # 初始资金 100,000,000
    cerebro.broker.setcash(1000000.0)
    # 佣金，双边各 0.0003
    cerebro.broker.setcommission(commission=0.0003)
    # 滑点：双边各 0.0001
    cerebro.broker.set_slippage_perc(perc=0.0001)
    # 设置单笔交易的数量 #########
    #cerebro.addsizer(...)
    # 添加策略 #########
    cerebro.addstrategy(TestStrategy)
    # 或者是添加调参策略（list用法）
    #cerebro.optstrategy(TestStrategy, cut_atr = [2,3,4,5])
    # 或者是添加调参策略（range用法）
    #cerebro.optstrategy(TestStrategy, cut_atr = range(2,5,1))
    # 添加策略分析指标 #########
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='pnl') # 返回收益率时序数据
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='_AnnualReturn') # 返回年初至年末的年度收益率
    cerebro.addanalyzer(bt.analyzers.Returns, _name='_Returns', tann=252)   #计算年化收益
    cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name='_SharpeRatio_A') # 计算年化夏普比率
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='_DrawDown') # 计算最大回撤相关指标
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='_TimeReturn')    # 返回收益率时序
    # 添加观测器 #########
    #cerebro.addobserver(...)
    # 启动回测 #########
    # 启动回测
    result = cerebro.run()
    # 从返回的 result 中提取回测结果
    strat = result[0]
    #策略调优时需要注释掉
    # 返回日度收益率序列
    daily_return = pd.Series(strat.analyzers.pnl.get_analysis())
    # 打印评价指标
    print("--------------- AnnualReturn -----------------")
    print(strat.analyzers._AnnualReturn.get_analysis())
    print("--------------- SharpeRatio -----------------")
    print(strat.analyzers._SharpeRatio_A.get_analysis())
    print("--------------- DrawDown -----------------")
    print(strat.analyzers._DrawDown.get_analysis())
    # 可视化回测结果 #########
    #cerebro.plot()
    colors = ['#729ece', '#ff9e4a', '#67bf5c', '#ed665d', '#ad8bc9', '#a8786e', '#ed97ca', '#a2a2a2', '#cdcc5d', '#6dccda']
    tab10_index = [3, 0, 2, 1, 2, 4, 5, 6, 7, 8, 9]
    cerebro.plot(iplot=False, 
                  style='lines', # 绘制线型价格走势，可改为 'candel'/lines 样式
                  lcolors=colors,
                  plotdist=0.1, 
                  bartrans=0.2, 
                  volup='#ff9896', 
                  voldown='#98df8a', 
                  loc='#5f5a41',
                  grid=False) # 删除水平网格


    #返回自定义的输出内容
    #######多参数回测模块
