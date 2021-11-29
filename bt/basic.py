import backtrader as bt # 导入 Backtrader
import backtrader.indicators as btind # 导入策略分析模块
import backtrader.feeds as btfeeds # 导入数据模块
import pandas as pd
from datetime import datetime
from bt.Data import Data as Data #导入bt本地数据模块
from apt.vendor.jqdata.base import base #导入jqta base模块
from apt.vendor.jqdata.jqdata import data as jqdata #导入jqta jqdata模块
from bt.Data import CustomData_PEPB as pe

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
    params = (('high_period',25),     #最高价的计算周期（日线默认25 小时线默认100）
            ('atr_period',14),)
    def log(self, txt, dt=None):
        '''可选，构建策略打印日志的函数：可用于打印订单记录或交易记录等'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        '''必选，初始化属性、计算指标等'''
        pass

    def notify_order(self, order):
        '''可选，打印订单信息'''
        pass

    def notify_trade(self, trade):
        '''可选，打印交易信息'''
        pass

    def next(self):
        '''必选，编写交易策略逻辑'''
        sma = btind.SimpleMovingAverage(...) # 计算均线
        pass

if __name__ == '__main__':
    # 实例化 cerebro #########
    cerebro = bt.Cerebro()
    ######### 通过 feeds 读取数据 #########
    d = Data()
    d.code = '002594.XSHE'
    d.start = datetime(2021,1,1)
    d.end = datetime(2021,12,31)
    d.ktype = '1d'
    d.myauth = False
    df_db = d.get_bt_data()
    ####标准的数据投喂
    #data = bt.feeds.PandasData(dataname = df_db)
    ####自定义数据投喂
    df_db['pe'] = 2 # 给原先的data1新增pe指标（简单的取值为2）
    df_db['pb'] = 3 # 给原先的data1新增pb指标（简单的取值为3）
    data = pe(dataname = df_db)
    #data = PandasData_more(dataname = df_db )
    #测试数据查询功能 
    print(df_db.query("index >= '2021/11/20' & index <='2021/11/29'"))
    # 将数据传递给 “大脑” #########
    cerebro.adddata(data , name = d.code) #自定义数据集的名称（用证券代码）
    ######### 通过经纪商设置初始资金 #########
    # 初始资金 100,000,000
    cerebro.broker.setcash(100000000.0)
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
    