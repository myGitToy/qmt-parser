"""
本模块是模拟一个基金换仓的例子
使用上证指数作为基准，每个季度对基金旗下的股票进行换仓操作
输出每日基金净值数据
"""
import backtrader as bt

from datetime import datetime
from apt.vendor.tspro.data import data as tsdata

class MonthlyRebalanceStrategy(bt.Strategy):
    params = (
        ('stocks_per_month', 10),  # 每月持有的股票数量
        ('rebalance_monthly', True),  # 是否每月换仓
        ('printlog', True),  # 是否打印日志
    )

    def log(self, txt, dt=None):
        ''' 日志函数 '''
        dt = dt or self.datas[0].datetime.date(0)
        if self.params.printlog:
            print(f'{dt.isoformat()}, {txt}')

    def __init__(self):
        self.order = None
        self.current_month = None
        self.stocks_to_hold = []  # 当前持有的股票列表

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入：{order.executed.price}')
            elif order.issell():
                self.log(f'卖出：{order.executed.price}')
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/拒绝')
        self.order = None

    def next(self):
        # 检查是否是月末
        current_date = self.datas[0].datetime.date(0)
        if self.current_month != current_date.month:
            self.current_month = current_date.month
            if self.params.rebalance_monthly:
                self.rebalance_portfolio()

    def rebalance_portfolio(self):
        # 实现换仓逻辑
        # 这里需要根据具体的换仓规则来实现，例如随机选择股票进行换仓
        # 更新self.stocks_to_hold列表，然后执行买卖操作

        # 示例：清空当前持仓，随机选择params.stocks_per_month个股票买入
        self.log('执行换仓')
        for stock in self.stocks_to_hold:
            self.sell(data=stock, size=10000)  # 卖出当前持有的股票
        self.stocks_to_hold = []  # 清空持仓列表

        # 随机选择新的股票进行买入（这里需要根据实际情况来选择股票）
        # 示例代码省略了选择股票的逻辑
        # for new_stock in selected_stocks:
        #     self.buy(data=new_stock, size=10000)
        #     self.stocks_to_hold.append(new_stock)

        # 输出当前仓位和基金净值
        self.log(f'当前仓位: {self.stocks_to_hold}')
        self.log(f'基金净值: {self.broker.getvalue()}')

# 添加数据、设置策略等代码省略

#测试数据读取
data = tsdata()
data.start_date = datetime(2024,6,19)
data.end_date = datetime(2024,6,28)
data.fq = tsdata.复权.动态复权
code_list = ['600530.SH', '600000.SH', '601398.SH', '601857.SH', '601988.SH']
for code in code_list:
    data.code = code
    df_bt = data.get_bt_data()
    df_k = data.get_k_data()
    print(df_bt)
    print(df_k)
    pass