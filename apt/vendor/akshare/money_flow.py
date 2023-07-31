import numpy as np
import pandas as pd
import tushare as ts
import akshare as ak
import sqlalchemy
from datetime import datetime
from apt.vendor.akshare.base import base as base
from apt.vendor.akshare.base import stock as stock
from apt.vendor.akshare.data import data as data2
from sqlalchemy.types import NVARCHAR , Float, Integer , Date

class money_flow(base , stock):
    """
    专门处理资金流向的类
    两种不同的资金流向：V1. 从tspro获取的传统资金流向（联网通过API方式）
                        V2. 从akshare 1分钟线价格 成交量转换过来的资金流向（从数据库获取）
    """
    def __init__(self):
        super(base , self).__init__()
        super(stock , self).__init__()
    def get_money_flow_V2(self , code = '600001.sh' , day = datetime(2023,1,1)):
        """
        从akshare 1分钟线价格 成交量转换过来的资金流向
        【输入】：
            code 证券代码
            day 交易日期
        """
        #交易日检查（暂未开通）
        super(base,self).
        self.
        a = data2()
        a.
        df.
        df2 = stock()
        df2.
        data = stock()
        data.code = code 
        self.et
        self.code = code
        self.end_date = day
        a = base()
        df = self.get_k_data().sort_values(by = ['date'] )
        print(df)
        #删除9:30和15:00的数据
        df = df.query('date.dt.time != datetime.strptime("09:30","%H:%M").time()')
        df = df.query('date.dt.time != datetime.strptime("15:00","%H:%M").time()')
        df['close_diff'] = df['close'] - df['close'].shift(1)
        #np.where单独使用，符合条件的返回array组，再使用iloc进行定位和修订
        df['money_flow'] = np.nan
        #df.iloc[np.where(df['close_diff'] > 0)]['money_flow'] = 1
        df['money_flow'] = np.where(df['close_diff'] > 0 , df['money'] , df['money_flow'] )
        df['money_flow'] = np.where(df['close_diff'] < 0 , -df['money'] , df['money_flow'] )
        df['money_flow'] = np.where(df['close_diff'] == 0 , 0 , df['money_flow'] )
        df['cumsum'] = df['money_flow'].cumsum()
        print(df)
        # 对时间进行一下处理
        df['date'] = pd.to_datetime(df['date'],format = "%m-%d")
        df.set_index('date',inplace=True)
        #print(df[['date','close','close_diff','money','money_flow','cumsum']])
        #统一各股资金流向的坐标轴，统一按照1个million来计算，也就是对应的1e7
        df['cumsum'] = df['cumsum'] / 1000000
        plt.rcParams['font.sans-serif']=['SimHei'] #用来正常显示中文
        plt.rcParams['axes.unicode_minus']=False #用来正常显示负号
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()    # mirror the ax1
        # 使用xticks
        # 这句是核心
        plt.xticks(range(0,len(df.index),100),list(df.index)[::100], rotation = 90)

        # 创建子图
        #graph_KAV = fig.add_subplot(1, 1, 1)
        mpf.candlestick2_ochl(ax1, df.open, df.close, df.high, df.low, width=0.5,colorup='r', colordown='g')  # 绘制K线走势
        plt.gcf().autofmt_xdate()  # 自动旋转日期标记

        #把X轴的时间进行转换，用来解决时间点断续的问题
        #ax1.plot(range(len(df.index)), df['close'], 'g-')
        ax2.plot(range(len(df.index)), df['cumsum'], 'b-')
        ax1.set_xlabel('时间')
        ax1.set_ylabel('价格', color='g')
        ax2.set_ylabel('资金流向（百万元人民币）', color='b')
        plt.title(f'{a.code}[{name}]:{a.start_date.date()}-{a.end_date.date()}资金流向表' )
        plt.show()
       
        pass
               
if __name__=="__main__":
    #测试资金流向
    a = money_flow()
    dd = a.get_1min_flow(code = '600389.sh' , day = datetime(2023,7,18))

    