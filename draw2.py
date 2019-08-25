# -*- coding: utf-8 -*-
import pandas as pd
import tushare as ts 
import matplotlib.pyplot as plt
import matplotlib.pyplot as savefig
from datetime import datetime
from datetime import timedelta, date
import matplotlib.dates as mdates
def picture(code):
    time=[]
    value=[]
    stock_info=pd.read_csv('.\\data\\day\\510300.csv')#历史行情
    print(stock_info)
    for i in range(len(stock_info)):
        time.append(stock_info[i][0])
        print(stock_info[i][0])
        value.append(stock_info[i][4])


    plt.figure(figsize=(10,3))
    xs = [datetime.strptime(d, '%Y-%m-%d').date() for d in time]
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator())
    plt.plot(xs,value,color="b",linewidth=1,marker='o',markerfacecolor='red',markersize=4)   #在当前绘图对象绘图（X轴，Y轴，蓝色虚线，线宽度）
    plt.gcf().autofmt_xdate()#时间旋转
    plt.xlabel("Time") #X轴标签  
    plt.ylabel("Price")  #Y轴标签  
    plt.title(code) #图标题
    plt.grid()#框线
    plt.savefig(code+".jpg") #保存图  
    plt.show()  #显示图

picture('510050')
