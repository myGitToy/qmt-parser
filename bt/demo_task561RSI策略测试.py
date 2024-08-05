"""
backtrader策略测试

"""

import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime
from apt.vendor.tspro.data import data as Data
class RsiStrategy(bt.Strategy):
    params = (
        ('ema_long_period', 200),
        ('ema_short_period', 5),
        ('rsi_period', 3),  #RSI周期
        ('rsi_overbought', 5),  #RSI超买线，默认低于5发出信号
        ('profit_percent', 0.93),
        ('hold_days', 5),
    )

    def __init__(self):
        self.ema_long = bt.indicators.EMA(self.data.close, period=self.params.ema_long_period)
        self.ema_short = bt.indicators.EMA(self.data.close, period=self.params.ema_short_period)
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        self.order = None
        self.buy_price = None
        self.buy_day = None

    def next(self):
        # 取消未完成的订单
        if self.order:
            self.cancel(self.order)
            self.order = None

        # 检查是否持有仓位
        if not self.position:
            #无持仓
            if self.data.close > self.ema_long and self.rsi < self.params.rsi_overbought:
                self.buy_price = self.data.close[0]
                self.buy_day = len(self)
                # 计算应买入的股数，假设每股价格为 self.buy_price，希望投入的金额为50000元
                size = 50000 / self.buy_price
                # 使用 buy 方法买入计算出的股数
                self.order = self.buy(size=int(size))  # 注意：这里使用 int() 确保股数为整数
        else:
            #有持仓 进入卖出逻辑
            if (len(self) - self.buy_day) > self.params.hold_days:
                self.order = self.sell()
            #if (len(self) - self.buy_day) > self.params.hold_days or self.data.close > self.ema_short or self.data.close < self.buy_price * self.params.profit_percent:
                #self.order = self.sell()

    def buy_logic(self):
        # 买入逻辑
        if self.data.close > self.ema_long and self.rsi < self.params.rsi_overbought:
            self.buy_price = self.data.close[0]
            self.buy_day = len(self)
            self.order = self.buy()
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
    d.code = '510300.SH'
    d.start = datetime(2022,1,1)
    d.end = datetime.now()
    d.ktype = '1d'
    df_db = d.get_k_data()
    df_db['datatime'] = pd.to_datetime(df_db['date'])
    df_db.set_index(["datatime"], inplace=True)
    #查询df_db中收盘价为0的数据
    print(df_db[df_db['close'] == 0])
    print(df_db)
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

    # 将数据传递给 “大脑” #########
    #cerebro.adddata(data , name = d.code) #自定义数据集的名称（用证券代码）
    cerebro.adddata(data)  #单代码标准用法
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
    cerebro.addstrategy(RsiStrategy)
    # 或者是添加调参策略（list用法）
    #cerebro.optstrategy(TestStrategy, cut_atr = [2,3,4,5])
    # 或者是添加调参策略（range用法）
    #cerebro.optstrategy(TestStrategy, cut_atr = range(2,5,1))
    # 添加策略分析指标 #########
    #cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='pnl') # 返回收益率时序数据
    #cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='_AnnualReturn') # 返回年初至年末的年度收益率
    #cerebro.addanalyzer(bt.analyzers.Returns, _name='_Returns', tann=252)   #计算年化收益
    #cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name='_SharpeRatio_A') # 计算年化夏普比率
    #cerebro.addanalyzer(bt.analyzers.DrawDown, _name='_DrawDown') # 计算最大回撤相关指标
    #cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='_TimeReturn')    # 返回收益率时序
    # 添加观测器 #########
    #cerebro.addobserver(...)
    # 启动回测 #########
    # 启动回测
    result = cerebro.run()
    # Add the Data Feed to Cerebro
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
    cerebro.plot()