import backtrader as bt # 导入 Backtrader
import backtrader.indicators as btind # 导入策略分析模块
import backtrader.feeds as btfeeds # 导入数据模块
import pandas as pd
import sqlalchemy
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
    params=(('high_period',25),     #最高价的计算周期（日线默认25 小时线默认100）
            ('atr_period',14),      #ATR的计算周期（日线默认14）
            ('prank_period',25),    #分位数的计算周期（日线默认25 小时线默认100）
            ('R',0.5),             #风险值R设定
            ('atr_size',0.5),         #ATR间隔 默认1个ATR间隔下订单
            ('unit_size',1),        #头寸大小 默认每次下单进行1个头寸
            ('open_separation',5),#清仓以后的再次开仓间隔（用来控制反复止损的参数）
            ('printlog',False),)     #是否输出日志 默认True
    def log(self, txt, dt=None):
        '''可选，构建策略打印日志的函数：可用于打印订单记录或交易记录等'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        '''必选，初始化属性、计算指标等'''
        self.dataclose = self.datas[0].close
        # 用于记录订单状态
        self.order = None
        #设置ATR指标
        self.atr = bt.indicators.AverageTrueRange(self.datas[0] , period = self.params.atr_period , plot = True , subplot= True , movav = bt.ind.MovAv.EMA)
        #设置头寸指标
        self.unit = self.cerebro.broker.getvalue() * self.params.R /100  / self.atr        
        #设置止损指标
        self.high_cut = bt.indicators.Highest(self.datas[0].close - self.atr * 2 , period = self.params.high_period , plot = True , subplot= False) 
        #设置EMA均线
        #self.ema = bt.talib.ema(self.datas[0].close , timeperiod = 5)
        #self.ema = bt.talib.talib.EMA(self.datas[0].close)

    def notify_order(self, order):
        '''可选，打印订单信息'''
        if order.status in [order.Submitted]:
            #cerebro已提交订单
            self.log(f"订单已提交，订单号：{order.ref}；提交价格：{order.price}；提交数量：{order.size}；订单状态：{order.Status[order.status]}"   )

        if order.status in [order.Accepted]:
            #交易所已接受订单
            #打印目前现有订单
            self.log(f"#########交易所接收到新订单，现存有效订单有：#######")
            for o in self.broker.get_orders_open():
                self.log(f"订单编号{o.ref}；订单价格{o.price:.3f}；订单数量{o.size};")
                
        if order.status in [order.Completed]:
            if order.isbuy():
                #self.log('BUY EXECUTED, Price: %.3f, Cost: %.3f, Comm %.2f' % (,order.executed.value,order.executed.comm))
                self.last_price = order.executed.price
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
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
                #加入队列
                #self.orefs.append(self.order)
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.3f, Cost: %.2f, Comm %.2f' %(order.executed.price,order.executed.value,order.executed.comm))
                pass
                #self.bar_executed = len(self)
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            #订单被交易所取消，判断是否需要重新下单
            pass
            self.log('****************************************Order Canceled/Margin/Rejected')

        #订单处理完成
        self.order = None

    def notify_trade(self, trade):
        '''可选，打印交易信息'''
        pass

    def next(self):
        '''必选，编写交易策略逻辑'''
        print(f"{self.datas[0].datetime.date()}:当前持仓量:{self.getposition(self.data).size}；持仓成本{self.getposition(self.data).price}；收盘价{self.datas[0].close[0]:.3f}")
        sma = btind.SimpleMovingAverage(...) # 计算均线
        ######获取仓位情况
        pos = self.getposition(self.data)
        ######获取交易所委托单情况
        #broker_order = self.broker.get_orders_open()
        if pos.size == 0  and len(self.broker.get_orders_open()) == 0:
            #持仓为0 且交易所订单列表为0，则进行下单
            #print(f'{self.datas[0].datetime.date()}:当前持仓量:{self.getposition(self.data).size}；收盘价{self.datas[0].close}' )
            #print(f"{self.datas[0].datetime.date():}无订单正在处理")
            #下单
            self.order = self.buy(exectype = bt.Order.StopLimit , price = 100 , size = 500 )
            self.order = self.buy(exectype = bt.Order.StopLimit , price = 150 , size = 500 )
        else:
            #有持仓，或者交易所有未成交订单，则显示当前未成交的订单
            #######使用自定义的队列来获取订单列表
            #for o in self.orefs:
                #订单状态：订单状态：{order.Status[order.status]}
                #self.log(f"订单编号{o.ref}；订单类型0买入1卖出：{o.ordtype}；订单价格{o.price:.3f}；订单数量{o.size};")
            #######使用broker来获取订单列表
            for o in self.broker.get_orders_open():
                self.log(f"[Broker]订单编号{o.ref}；订单类型：{o.ordtype}；订单价格{o.price:.3f}；订单数量{o.size};订单类型{o.Status[o.status]}")

if __name__ == '__main__':
    # 实例化 cerebro #########
    cerebro = bt.Cerebro()
    ######### 通过 feeds 读取数据 #########
    d = Data()
    d.code = '002594.XSHE'
    d.start = datetime(2020,2,1)
    d.end = datetime(2021,10,9)
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
    # 添加策略分析指标 #########
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='pnl') # 返回收益率时序数据
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='_AnnualReturn') # 年化收益率
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='_SharpeRatio') # 夏普比率
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='_DrawDown') # 回撤
    # 添加观测器 #########
    #cerebro.addobserver(...)
    # 启动回测 #########
    # 启动回测
    result = cerebro.run()
    # 从返回的 result 中提取回测结果
    strat = result[0]
    # 返回日度收益率序列
    daily_return = pd.Series(strat.analyzers.pnl.get_analysis())
    # 打印评价指标
    print("--------------- AnnualReturn -----------------")
    print(strat.analyzers._AnnualReturn.get_analysis())
    print("--------------- SharpeRatio -----------------")
    print(strat.analyzers._SharpeRatio.get_analysis())
    print("--------------- DrawDown -----------------")
    print(strat.analyzers._DrawDown.get_analysis())
    # 可视化回测结果 #########
    cerebro.plot()
    """
    colors = ['#729ece', '#ff9e4a', '#67bf5c', '#ed665d', '#ad8bc9', '#a8786e', '#ed97ca', '#a2a2a2', '#cdcc5d', '#6dccda']
    tab10_index = [3, 0, 2, 1, 2, 4, 5, 6, 7, 8, 9]
    cerebro.plot(iplot=False, 
                  style='lines', # 绘制线型价格走势，可改为 'candel' 样式
                  lcolors=colors,
                  plotdist=0.1, 
                  bartrans=0.2, 
                  volup='#ff9896', 
                  voldown='#98df8a', 
                  loc='#5f5a41',
                  grid=False) # 删除水平网格
    """

    #返回自定义的输出内容
    