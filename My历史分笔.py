import tushare as ts
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

"""
目前测试模块将交易的time列作为时间序列并设置为索引（加入了日期，目前无法解决只显示HH:MM:SS）
索引上可以进行重采样，按照1分钟的频率进行汇总，目的是为了和分时图进行叠加
重采样后的数据删除了9:25-9:30/11:30-13:00之间的空数据，但是绘图后仍会留下空白区间目前无法解决
重采样前一定要做好买卖分离，因为采样后的sum()过程会把买卖信息删除，因为文本列无法做汇总

"""
#df = ts.get_realtime_quotes('159949') #当日实时买盘 卖盘挂单 支持ETF
#print(df[['b1_v','b1_p','a1_v','a1_p']])
day='2020-11-13'  #时间格式必须是YYYY-MM-DD
code='159996'
df = ts.get_tick_data(code,date=day,src='tt')   #历史分笔交易  支持ETF 基本上为每隔三秒左右生成的合并数据，
print(df)
#保存原始数据至指定文件
#df.to_csv('.\\data\\%s_tick_data_%s.csv' % (code,day), encoding = 'utf_8_sig')
#设置格式
df['time'] = day + ' ' + df['time']
df['time'] = pd.to_datetime(df['time']  )
#设置索引
df.set_index('time',inplace=True)
#买卖分离
df['amount']=np.where(df['type'] == '卖盘' , - df['amount'] , df['amount'])
df['amount']=np.where(df['type'] == '中性盘' , 0 , df['amount'])
#删除首尾行
#print(df.drop(df.index[:1]))
df = df.iloc[1:-1] 
#时间重采样
re = df.resample('1min').sum()
print(re)
#去除价格为0 丢弃11:30-13：00中间休息时间 但不会影响绘图，因为时间序列作图会填充丢失的时间
re = re[re['price'] !=0]
#保存时间序列至指定文件
#re.to_csv('.\\data\\%s_tick_data_%s_1min.csv' % (code,day), encoding = 'utf_8_sig')
re['资金流入'] = re['amount'].cumsum()
#统一各股资金流向的坐标轴，统一按照1个million来计算，也就是对应的1e7
re['资金流入'] = re['资金流入'] / 1000000
re['资金流入'].plot()
#设置标题
plt.rcParams['font.sans-serif']=['SimHei'] #用来正常显示中文
plt.rcParams['axes.unicode_minus']=False #用来正常显示负号
plt.xlabel('时间')
plt.ylabel('资金流向（百万元人民币）')
plt.title('%s %s 资金流向表' % (day,code))
plt.show()
