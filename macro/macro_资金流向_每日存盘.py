from datetime import datetime ,timedelta
import numpy as np
import tushare as ts
import pandas as pd
import matplotlib.pyplot as plt
import mpl_finance as mpf  # 替换 import matplotlib.finance as mpf
from apt.qsp_universal.base import base as data
# 列名与数据对其显示
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
# 显示所有列
#pd.set_option('display.max_columns', None)
############1. 基础设置
a = data()
a.end_date = datetime.now()
a.start_date = a.end_date - timedelta(days = 30)
a.fq = data.复权.动态复权
a.ktype = '1m'
a.vendor = a.vendor.tusharePro


############2. 读取自选股
df_code_main = pd.DataFrame()
#读取第一张表格
df_code1 = data.read_excel(file_name = '.\\data\\海龟模型\\自选股列表.xlsx' , sheet_name = '33指数')
#读取第二张表格
df_code2 = data.read_excel(file_name = '.\\data\\海龟模型\\自选股列表.xlsx' , sheet_name = '自选股')
#读取第三张表格
df_code3 = data.read_excel(file_name = '.\\data\\海龟模型\\自选股列表.xlsx' , sheet_name = 'ETF')
#合并表格
df_code_main = pd.concat([df_code_main, df_code1 , df_code2 , df_code3] , sort = False)
#更改列名
df_code_main.rename(columns={"证券代码": "code", "证券名称": "name"} , errors="raise" , inplace = True)
#去重
df_code_main.drop_duplicates(subset = ['code'], keep = 'first', inplace = True)
#证券代码列表
code_list = df_code_main['code'].tolist()


for code in code_list:
    a.code = code
    name = a.get_security(code = a.code)[0].iloc[0].at['name']    #获取证券名称
    df = a.get_k_data().sort_values(by = ['date'] )
    #删除9:30和15:00的数据（日线重采样不删除头尾数据）
    #逻辑是头尾数据的价格变化也是由资金导致的，因此日线不受影响
    #df = df.query('date.dt.time != datetime.strptime("09:30","%H:%M").time()')
    #df = df.query('date.dt.time != datetime.strptime("15:00","%H:%M").time()')
    df['close_diff'] = df['close'] - df['close'].shift(1)
    #np.where单独使用，符合条件的返回array组，再使用iloc进行定位和修订
    df['money_flow'] = np.nan
    #df.iloc[np.where(df['close_diff'] > 0)]['money_flow'] = 1
    df['money_flow'] = np.where(df['close_diff'] > 0 , df['money'] , df['money_flow'] )
    df['money_flow'] = np.where(df['close_diff'] < 0 , -df['money'] , df['money_flow'] )
    df['money_flow'] = np.where(df['close_diff'] == 0 , 0 , df['money_flow'] )
    df['cumsum'] = df['money_flow'].cumsum()
    # 对时间进行一下处理
    df['date'] = pd.to_datetime(df['date'],format = "%m-%d")
    df.set_index('date',inplace=True)
    #数据重采样
    df = df.resample('30min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum','money':'sum','factor':'first','cumsum':'last'}).dropna(axis=0)
    #df_db = df_db.resample('D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum','money':'sum','factor':'first'}).dropna(axis=0)
    #print(df[['date','close','close_diff','money','money_flow','cumsum']])
    #统一各股资金流向的坐标轴，统一按照1个million来计算，也就是对应的1e7
    df['cumsum'] = df['cumsum'] / 1000000
    plt.rcParams['font.sans-serif']=['SimHei'] #用来正常显示中文
    plt.rcParams['axes.unicode_minus']=False #用来正常显示负号
    fig, ax1 = plt.subplots(figsize = (12,6))
    ax2 = ax1.twinx()    # mirror the ax1
    # 使用xticks
    # 这句是核心
    #plt.xticks(range(0,count,int(count/50)),list(df.index)[::int(count/50)], rotation = 30)
    plt.xticks(range(0,len(df.index),10),list(df.index)[::10], rotation = 30)

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
    plt.savefig(f'.\\data\\资金流向\\{a.code}-{name}.png' , dpi = 300)
    #plt.show()

