import numpy as np
import pandas as pd
import tushare as ts
import akshare as ak
import sqlalchemy
from scipy import stats
from datetime import datetime
#from apt.vendor.akshare.base import base as base
#from apt.vendor.akshare.base import stock as stock
from apt.vendor.akshare.data import data as akdata
from apt.vendor.tspro.money_flow import money_flow as ts_flow
from sqlalchemy.types import NVARCHAR , Float, Integer , Date
from apt.vendor.tspro.security import security as sec
"""
数据词典：
表名：stock_money_flow
id	int			True	False	1	
code	varchar	10		False	False		证券代码
date	date			False	False		日期
source	varchar	6		False	False		数据来源（ak/tspro）
ktype	varchar	6		False	False		数据类型（1m/5m/60m/1d）
volatility	decimal	10	6	False	False		波动比率（单位 百分比 正代表流入 负代表流出 存储时保留小数点后6位）
money_flow	decimal	18	2	False	False		资金流向（单位 元 正代表流入 负代表流出 ）
is_error	smallint			False	False		是否错误 0/1（1代表无数据，即有1d数据但是无分时数据，无法计算出资金流向）

表名：tspro_money_flow（使用tspro的资金流向数据，通过API获取并保存本地，非本地分时线计算）
date	date			True	False	1	日期
code	varchar	12		True	False	2	股票代码
buy_sm_vol	int			False	False		小单买入量（手）
buy_sm_amount	decimal	12	4	False	False		小单买入金额（万元）
sell_sm_vol	int			False	False		小单卖出量（手）
sell_sm_amount	decimal	12	4	False	False		小单卖出金额（万元）
buy_md_vol	int			False	False		中单买入量（手）
buy_md_amount	decimal	12	4	False	False		中单买入金额（万元）
sell_md_vol	int			False	False		中单卖出量（手）
sell_md_amount	decimal	12	4	False	False		中单卖出金额（万元）
buy_lg_vol	int			False	False		大单买入量（手）
buy_lg_amount	decimal	12	4	False	False		大单买入金额（万元）
sell_lg_vol	int			False	False		大单卖出量（手）
sell_lg_amount	decimal	12	4	False	False		大单卖出金额（万元）
buy_elg_vol	int			False	False		特大单买入量（手）
buy_elg_amount	decimal	12	4	False	False		特大单买入金额（万元）
sell_elg_vol	int			False	False		特大单卖出量（手）
sell_elg_amount	decimal	12	4	False	False		特大单卖出金额（万元）
net_mf_vol	int			False	False		净流入量（手）
net_mf_amount	decimal	12	4	False	False		净流入额（万元）
trade_count	int			False	False		交易笔数
"""
class money_flow(akdata):
    """
    专门处理资金流向的类
    两种不同的资金流向：V1. 从tspro获取的传统资金流向（联网通过API方式）
                        V2. 从akshare 1分钟线价格 成交量转换过来的资金流向（从数据库获取） 对应calculate_money_flow_min方法
    """
    def daily_update(self , sleep = 0.2):
        """
        每日资金流向更新（按日更新）
        此处实际调用vendor.tspro下面的方法
        """
        #获取更新列表（按交易日）
        return ts_flow.daily_update(self , sleep = sleep)

    def get_money_flow(self , rolling_list = [3,5,10,20,30,60,120] , to_excel = False):
        """
        获取资金流向(tspro资金流向) 
        此处实际调用vendor.tspro下面的方法
        """
        return ts_flow.get_money_flow(self , rolling_list = rolling_list , to_excel = to_excel)

    def get_money_flow_1min(self , rolling_list = [3,5,10,20,30,60,120] , to_excel = False):
        """
        从akshare 1分钟线价格 成交量转换过来的资金流向（这里使用的简单逻辑流，1分钟线收盘上涨代表全部资金流入，反之亦然）
        备注：这部分是老逻辑和老代码，尽量不要使用
        【输入】
            self.code 证券代码
            day 日期
        【返回】
            单个代码在指定日期区间的资金流向（万元）
        """
        #交易代码校验（跳过）
        #原因：1分钟线数据支持stock类和etf类
        #获取数据（强制使用1分钟线）
        self.ktype = '1m'
        df_db = self.get_k_data().sort_values(by = ['date'] )
        #初始化最后需要输出的DataFrame
        df_flow = pd.DataFrame(columns = [['money_flow']], index = df_db['date'].dt.date.unique())
        #distinct_dates['date'] = df_db['date'].dt.date.unique()
        #distinct_dates['date'] = pd.to_datetime(df_db['date'].dt.date.unique()) #时间日期ns64化
        series_days = df_db['date'].dt.date.unique()
        #print(distinct_dates.shape[0])
        for day in series_days:
            #print(day)
            df = df_db.query('date.dt.date == @day')
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
            df_flow.loc[day,'money_flow'] = df.iloc[-1]['cumsum'] /10000
            #print(distinct_dates)
        #对输出的df进行调整，列 code|date|money_flow
        df_flow['code'] = self.code
        df_flow = df_flow.rename_axis('date').reset_index()
        #df_flow['money_flow'] = df_flow['money_flow'].apply(lambda x: format(x, '.2f'))
        #df_flow['date'] = pd.to_datetime(df_flow['date'])
        #print(df_flow)
        #基础资金流向列表的计算
        for n in rolling_list:
            #滚动窗口累计计算
            df_flow[f'money_flow_r{n}'] = df_flow['money_flow'].rolling(n).sum()
            #分位数计算
            df_flow[f'money_flow_p{n}'] =  df_flow[f'money_flow_r{n}'].rolling(n).apply(lambda x: stats.percentileofscore(x, x.iloc[-1]))
        if to_excel ==True:
            #输出EXCEL
            df_flow.to_excel(f'.\\data\\测试数据\\资金流向_1min_{self.code}.xlsx', sheet_name = f'sheet1' ,  header = True, index = True)
        #print(df_flow)
        return df_flow

    def calculate_money_flow_min(self , stock_data = None , date = None , to_excel = False):
        """
        计算基于分时线的资金流向(使用akshare分时数据，默认为1分钟线) 
        【输入】
            stock_data 传入的DataFrame数据 默认为None 如果为None，则自行获取
            date 日期 默认为None 如果为None，则使用self.start_date和self.end_date区间
            code 证券代码 使用self.code
        【返回】
            返回值 非聚合的分时数据+波动比率和净资金流向
            dataframe 数据结构：传统的分时线DataFrame数据+波动比率和净资金流向两列        
        """
        ###  数据校验部分  ###
        if self.ktype is None or self.ktype == '1d':
            self.ktype = '1m' #默认使用1分钟线
        if stock_data is None:
            #无原始传入的数据：获取1m数据          
            self.stock_data = self.get_k_data()
        else:
            # 检查数据：查看是否包含open, high, low, close, money列
            required_columns = {'open', 'high', 'low', 'close', 'money'}
            if not required_columns.issubset(stock_data.columns):
                raise ValueError(f"传入的数据必须包含以下列: {required_columns}")
            # 有原始传入的数据：复制数据以避免修改原始数据
            self.stock_data = stock_data.copy()
        # 检查数据的有效性（self.stock_data的open列任意行不能为0）
        if self.stock_data['open'].eq(0).any():
            raise ValueError("数据中包含开盘价为0的行，无法计算资金流向。请检查数据的有效性。")

        ###  逻辑计算部分  ###
        # 计算波动比率：(收盘价-开盘价)/(最高价-最低价)
        # 【重要备注】：这里不采用前收的数据，仅计算盘中的情绪和资金走势。因此如果分时的第一根数据，也就是开盘9：30的数据为高开，随后低走，则认为是资金流出
        self.stock_data['波动比率'] = self.stock_data.apply(
            lambda row: (row['close'] - row['open']) / (row['high'] - row['low'])
            if (row['high'] != row['low'] and pd.notnull(row['open'])) else 0, axis=1
        )
        # 计算资金流向：波动比率 * 成交金额
        self.stock_data['净资金流向'] = self.stock_data['波动比率'] * self.stock_data['money']
        
        # 转换单位和保留小数点位数
        self.stock_data['净资金流向'] = (self.stock_data['净资金流向']).round(2)  # 保留2位小数（单位 元）
        self.stock_data['波动比率'] = self.stock_data['波动比率'].round(4)  # 波动比率保留4位小数
        
        if to_excel ==True:
            #输出EXCEL
            self.stock_data.to_excel(f'.\\data\\测试数据\\资金流向_{self.ktype}_{self.code}.xlsx', sheet_name = f'sheet1' ,  header = True, index = True)
        
        return self.stock_data
        # 计算聚合数据
        total_money = self.stock_data['money'].sum()
        total_net_flow = self.stock_data['净资金流向'].sum()
        
        # 计算聚合波动比率 = 当天净资金流向/总money
        aggregated_volatility_ratio = (total_net_flow / total_money) if total_money != 0 else 0
        # 返回包含聚合结果的Series
        result = {
            '波动比率': aggregated_volatility_ratio,
            '净资金流向': total_net_flow
        }

        return pd.Series([result['波动比率'], result['净资金流向']], index=['波动比率', '净资金流向'])
        # 返回聚合后的json，包含波动比率，净资金流向
        json_result = {
            '波动比率': aggregated_volatility_ratio,
            '净资金流向': total_net_flow,
        }
        return json_result

        # 计算资金流向：波动比率 * 成交金额
        df['净资金流向'] = df['波动比率'] * df['money']
        
        # 转换单位和保留小数点位数
        df['净资金流向'] = (df['净资金流向'] / 1000000).round(1)  # 转换为百万并保留1位小数
        df['波动比率'] = df['波动比率'].round(2)  # 波动比率保留2位小数
        
        # 为了保持与之前代码的一致性，还可以计算积极流入和消极流出
        df['积极流入'] = df['净资金流向'].apply(lambda x: x if x > 0 else 0)
        df['消极流出'] = df['净资金流向'].apply(lambda x: -x if x < 0 else 0)
        
        return df        
        pass



if __name__=="__main__":
    #测试资金流向
    money = money_flow()
    money.code = '688349.sh'
    money.start_date = datetime(2025,9,1)
    money.end_date = datetime.now()
    money.ktype = '1d'
    df_1d = money.get_k_data()
    print(df_1d)
    money.ktype = '5m'
    df_result = money.calculate_money_flow_min()
    print(df_result)
