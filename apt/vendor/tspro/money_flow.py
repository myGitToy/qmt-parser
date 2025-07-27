import numpy as np
import pandas as pd
import tushare as ts
import sqlalchemy
import time
#from apt.qsp_universal.base import base as kdata
#from apt.vendor.akshare.base import base as akdata
#import datetime
from scipy import stats
from datetime import datetime,timedelta
#from apt.vendor.tspro.base import base as base
from apt.vendor.tspro.data import data as tspro_data
from apt.vendor.tspro.security import security as sec

class money_flow(tspro_data):
    """
    专门处理资金流向的类
    模块的结构说明文档详见
    https://huiqiao.visualstudio.com/MyFunds/_sprints/taskboard/MyFunds%20Team/MyFunds/2023Q3?workitem=489
    """
    #def __init__(self):
        #声明父类的init方法，也可以选择不声明
        #super().__init__()

    def daily_update(self , sleep = 0.2):
        """
        每日资金流向更新（按日更新）
        原始jqdata是按代码更新的，新逻辑按日期进行更新   
        数据起始日期为2007年(2007年上半年的数据不太稳定，有部分日期缺失)
        """
        #获取更新列表（按交易日）
        se = sec()
        se.start_date = self.start_date
        se.end_date = self.end_date
        trade_day = pd.DataFrame(columns = ['date'])
        trade_day = se.get_calendar(is_open = 1)
        #获取资金流向库中存在的日期列表
        query_daysql = f"select distinct date FROM tspro_money_flow FORCE INDEX (main) WHERE date BETWEEN '{self.start_date.date()}' and '{self.end_date.date()}'  ORDER BY date asc" 
        df_dbday = pd.read_sql_query(query_daysql , self.engine)
        if df_dbday.empty == True:
            #数据库不存在数据
            df_dbday = pd.DataFrame(columns = ['date'])
        else:
            #数据库存在数据
            df_dbday['date'] = pd.to_datetime(df_dbday['date']) #时间日期ns64化
            pass
        #数据拼接，最终需要更新的日期是trade_day中包含且df_dbday不包含的数据
        day_diff = pd.concat([trade_day , df_dbday , df_dbday]).drop_duplicates(subset = ['date'] , keep = False)
        #print(day_diff)
        #打印标题
        print("############正在准备更新资金流向信息###########")
        """
        更新逻辑：
            1. 需要更新的日期
                1.1 取出区间内的交易日
                1.2 取出数据库中存在资金流向的日期
                1.3 两者取差集就是需要更新的日期
            2. 按照日期循环，获取每日的资金流向
            3. 数据写入数据库
        逻辑优点和不足：
            1. 一次性提取每日的资金流向，运行效率较高
            2. 智能化更新，跳过重复的日期
            3. 缺点：更新限制每次5000条，后续可能会超过限制值
        """
        for day in day_diff['date']:
            #获取数据库中存在的数据最后更新日期（加入强制使用索引的内容）
            df = self.pro.moneyflow(trade_date = day.strftime("%Y%m%d"), fields=[
                                                                        "ts_code",
                                                                        "trade_date",
                                                                        "buy_sm_vol",
                                                                        "buy_sm_amount",
                                                                        "sell_sm_vol",
                                                                        "sell_sm_amount",
                                                                        "buy_md_vol",
                                                                        "buy_md_amount",
                                                                        "sell_md_vol",
                                                                        "sell_md_amount",
                                                                        "buy_lg_vol",
                                                                        "buy_lg_amount",
                                                                        "sell_lg_vol",
                                                                        "sell_lg_amount",
                                                                        "buy_elg_vol",
                                                                        "buy_elg_amount",
                                                                        "sell_elg_vol",
                                                                        "sell_elg_amount",
                                                                        "net_mf_vol",
                                                                        "net_mf_amount",
                                                                        "trade_count"
                                                                    ])
            #重命名列（money_flow中的证券代码sec_code和数据库中的不一致）
            df.rename(columns = {'ts_code':'code','trade_date':'date'} , inplace = True)
            df['date'] = pd.to_datetime(df['date']) #时间日期ns64化
            #保存至数据库 
            if df.empty == True:
                print(f"{day.date()}数据为空，跳过上传")
            else:
                df.to_sql(
                        name = 'tspro_money_flow',
                        con = self.engine,
                        index = False,
                        if_exists = 'append')
                print(f"{day.date()} 数据已上传完成，更新条目数{df.shape[0]} (money flow)")
                time.sleep(sleep)

    def get_money_flow(self , rolling_list = [3,5,10,20,30,60,120] , to_excel = False):
        """
        获取资金流向(tspro资金流向) 
        ['3','5','10','20','30','60','120']
        各类别统计规则如下：
        小单：5万以下 中单：5万～20万 大单：20万～100万 特大单：成交额>=100万
        只能按照日线数据获取        
        输入：
            rolling_list 需要回滚的日期列表
            to_excel 是否保存到excel文档（这里没想好是excel文件还是csv文件）
        返回：
            DataFrame
        其他说明：
            目前的问题：
                中单+小单 = -（大单+超大单）
                buy_net = sell_net
                上述两点从逻辑上是讲不通的，因此整个模块的数据现在就是存在问题
        """
        #获取基础信息

        #判断是否是stock类型 且有数据
        if  sec.get_security(self , code = self.code)[1] !='stock':
            raise ValueError(f'请检查证券代码:{self.code}非stock类代码')

        #获取资金流向
        df = pd.read_sql_query(f"select * from tspro_money_flow where code = '{self.code}' and date between '{self.start_date.date()}' and '{self.end_date.date()}' order BY date" , self.engine)
        #基础资金流向列表的计算
        df['小单净额'] = df['buy_sm_amount'] - df['sell_sm_amount']
        df['中单净额'] = df['buy_md_amount'] - df['sell_md_amount']
        df['大单净额'] = df['buy_lg_amount'] - df['sell_lg_amount']
        df['超单大净额'] = df['buy_elg_amount'] - df['sell_elg_amount']
        df['散户净额'] = df['小单净额'] + df['中单净额']
        df['主力净额'] = df['大单净额'] + df['超单大净额']
        df['总净额'] = df['net_mf_amount']
        for n in rolling_list:
            #滚动窗口累计计算
            #df[f'小单金额_r{n}'] = df['小单净额'].rolling(n).mean().apply(lambda x: '%.2f'%x)  #小数点截取范例
            df[f'小单金额_r{n}'] = df['小单净额'].rolling(n).sum()
            df[f'中单净额_r{n}'] = df['中单净额'].rolling(n).sum()
            df[f'大单净额_r{n}'] = df['大单净额'].rolling(n).sum()
            df[f'超单大净额_r{n}'] = df['超单大净额'].rolling(n).sum()
            df[f'散户净额_r{n}'] = df['散户净额'].rolling(n).sum()
            df[f'主力净额_r{n}'] = df['主力净额'].rolling(n).sum()
            df[f'总净额_r{n}'] = df['总净额'].rolling(n).sum()
            #滚动窗口
            df[f'小单金额_p{n}'] =  df[f'小单金额_r{n}'].rolling(n).apply(lambda x: stats.percentileofscore(x, x.iloc[-1]))
            df[f'中单净额_p{n}'] =  df[f'中单净额_r{n}'].rolling(n).apply(lambda x: stats.percentileofscore(x, x.iloc[-1]))
            df[f'大单净额_p{n}'] =  df[f'大单净额_r{n}'].rolling(n).apply(lambda x: stats.percentileofscore(x, x.iloc[-1]))
            df[f'超单大净额_p{n}'] =  df[f'超单大净额_r{n}'].rolling(n).apply(lambda x: stats.percentileofscore(x, x.iloc[-1]))
            df[f'散户净额_p{n}'] =  df[f'散户净额_r{n}'].rolling(n).apply(lambda x: stats.percentileofscore(x, x.iloc[-1]))
            df[f'主力净额_p{n}'] =  df[f'主力净额_r{n}'].rolling(n).apply(lambda x: stats.percentileofscore(x, x.iloc[-1]))
            df[f'总净额_p{n}'] =  df[f'总净额_r{n}'].rolling(n).apply(lambda x: stats.percentileofscore(x, x.iloc[-1]))
            #设置格式（格式设置会使输出的数字采用文本方式保存，所以这里暂时不启用）
            #df[f'小单金额_p{n}'] =  df[f'小单金额_p{n}'].apply(lambda x: '%.2f'%x) 
            #df[f'中单净额_p{n}'] =  df[f'中单净额_p{n}'].apply(lambda x: '%.2f'%x) 
            #df[f'大单净额_p{n}'] =  df[f'大单净额_p{n}'].apply(lambda x: '%.2f'%x) 
            #df[f'超单大净额_p{n}'] =  df[f'超单大净额_p{n}'].apply(lambda x: '%.2f'%x) 
            #df[f'散户净额_p{n}'] =  df[f'散户净额_p{n}'].apply(lambda x: '%.2f'%x) 
            #df[f'主力净额_p{n}'] =  df[f'主力净额_p{n}'].apply(lambda x: '%.2f'%x) 
        if to_excel ==True:
            #输出EXCEL
            df.to_excel(f'.\\data\\测试数据\\资金流向{self.code}.xlsx', sheet_name = f'sheet1' ,  header=True, index=False)
        return df
    def get_cal_k(self , rolling_list = [3,5,10,20,30,60,120] , to_csv = False):
        """
        获取计算后的K线数据
        
        """
        ###取出区间内的K线数据
        self.ktype = '1d'
        df =  self.get_k_data()
        df = df[['date','code','close','money']]
        for n in rolling_list:
            #滚动窗口累计计算
            df[f'money_r{n}'] = df['money'].rolling(n).sum()
            #分位数计算
            df[f'close_p{n}'] =  df['close'].rolling(n).apply(lambda x: stats.percentileofscore(x, x.iloc[-1]))
            #df[f'money_p{n}'] =  df[f'money_r{n}'].rolling(n).apply(lambda x: stats.percentileofscore(x, x.iloc[-1]))
        if to_csv ==True:
            #输出csv文件
            df.to_excel(f'.\\data\\测试数据\\K线数据_{self.code}.xlsx', sheet_name = f'sheet1' ,  header = True, index = True)
        #print(df_flow)
        return df
if __name__=="__main__":
    #模块参数初始化
    money = money_flow()
    money.code = '600519.sh'
    money.start_date = datetime(2021,1,1)
    money.end_date = datetime(2023,7,31)
    money.ktype = '1m'
    df = money.get_cal_k(to_csv = True)
    print(df)