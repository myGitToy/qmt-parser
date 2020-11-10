import tushare as ts
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
code='000001'
#df = ts.get_tick_data(code,date=day,src='tt')   #历史分笔交易  支持ETF 基本上为每隔三秒左右生成的合并数据，
df = ts.get_today_ticks(code)
#首尾行颠倒
df = df[::-1]
#删除首行，不删除尾行因为是实时内容，没有收盘
df = df.iloc[1:] 
#数据保存
#df.to_csv('.\\data\\%s_实时明细.csv' % (code), encoding = 'utf_8_sig')
print(df)
#设置格式
if df.empty != True:
    #有数据
    df['amount'].astype(np.float)
    #设置索引
    df.set_index('time' , inplace = True)
    df['amount'] = np.where(df['type'] == '卖盘' , -df['amount'] , df['amount'])
    df['amount'] = np.where(df['type'] == '中性盘' , 0 , df['amount'])
    df['资金流入'] = df['amount'].cumsum()
    #统一各股资金流向的坐标轴，统一按照1个million来计算，也就是对应的1e7
    df['资金流入'] = df['资金流入'] / 1000000
    print(df)
    df['资金流入'].plot()
    #设置标题
    plt.rcParams['font.sans-serif']=['SimHei'] #用来正常显示中文
    plt.rcParams['axes.unicode_minus']=False #用来正常显示负号
    plt.xlabel('时间')
    plt.ylabel('资金流向（百万元人民币）')
    plt.title('%s 当日实时资金流向表' % (code))
    plt.show()