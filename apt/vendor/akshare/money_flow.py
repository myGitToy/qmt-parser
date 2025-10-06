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
        tspro中的每日资金流向更新（按日更新）
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
        指定代码和日期区间，获取get_k_data后进行本地计算，无需通过stock_money_flow表
        【输入】
            stock_data 传入的DataFrame数据 默认为None 如果为None，则自行获取
            date 日期 默认为None 如果为None，则使用self.start_date和self.end_date区间
            code 证券代码 使用self.code
        【返回】
            返回值 非聚合的分时数据+波动比率和净资金流向
            dataframe 数据结构：传统的分时线DataFrame数据+波动比率和净资金流向两列(注意：数据未聚合)        
        """
        ###  数据校验部分  ###
        if self.ktype is None or self.ktype == '1d':
            self.ktype = '1m' #默认使用1分钟线
        if stock_data is None:
            #无原始传入的数据：获取1m数据          
            self.stock_data = self.get_k_data()
            # 是否有分时数据的校验
            if self.stock_data.empty:
                return pd.DataFrame() #无数据则返回空的DataFrame
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
        self.stock_data['分时股价波动比率'] = self.stock_data.apply(
            lambda row: (row['close'] - row['open']) / (row['high'] - row['low'])
            if (row['high'] != row['low'] and pd.notnull(row['open'])) else 0, axis=1
        )
        # 计算资金流向：波动比率 * 成交金额
        self.stock_data['净资金流向'] = self.stock_data['分时股价波动比率'] * self.stock_data['money']
        
        # 转换单位和保留小数点位数
        self.stock_data['净资金流向'] = (self.stock_data['净资金流向']).round(2)  # 保留2位小数（单位 元）
        # 备注：此处的波动比例是针对股价波动而言的，与后续计算的资金流向比率无关
        self.stock_data['分时股价波动比率'] = self.stock_data['分时股价波动比率'].round(4)  # 波动比率保留4位小数
        
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

    def update_money_flow_min(self):
        """
        更新基于分时线的资金流向(使用akshare分时数据，默认为1分钟线) 
        全量更新，无法单独选择某个code
        【输入】
            默认无需输入 self.code 证券代码
            默认无需输入 self.start_date 起始日期
            默认无需输入 self.end_date 结束日期
            默认无需输入 self.ktype 分钟线类型 1m/5m/60m
        【更新逻辑】
            1. 批量获取tspro_1d中的数据，差集写入stock_money_flow（source使用ak）
            2. 从stock_money_flow中获取待更新的数据（is_error为空），逐日计算分时资金流向

        """
        # 全局设置
        my_source = 'ak'
        # 对ktype进行校验
        if self.ktype is None or self.ktype == '1d':
            self.ktype = '1m' #默认使用1分钟线

        ######## 基于tspro_1d 进行差集更新
        # 查询日线数据 
        # 备注 2025/1/1-2025/9/30 数据获取大概需要3.3秒
        sql_1d = f"select code,date from tspro_1d where date >= '{self.start_date.date()}' and date <= '{self.end_date.date()}'"
        # 查询money_flow表的数据
        sql_flow = f"select code,date from stock_money_flow where source = '{my_source}' and ktype = '{self.ktype}' and date >= '{self.start_date.date()}' and date <= '{self.end_date.date()}'"
        # 检查差集数据
        df_1d = pd.read_sql(sql_1d , self.engine)
        df_flow = pd.read_sql(sql_flow , self.engine)
        if df_1d.empty:
            print(f'tspro_1d在{self.start_date.date()}到{self.end_date.date()}区间无日线数据，无法差集写入')
            return None
        if df_flow.empty:
            df_diff = df_1d #stock_money_flow表中对应日期区间无数据，全部插入
        else:
            # 数据统一格式
            df_1d['date'] = pd.to_datetime(df_1d['date'])
            df_flow['date'] = pd.to_datetime(df_flow['date'])
            df_diff = pd.merge(df_1d, df_flow, on=['code', 'date'], how='left', indicator=True)
            df_diff = df_diff[df_diff['_merge'] == 'left_only'].drop(columns=['_merge'])
        # 增加其他有效数据列 source=ak ktype=self.ktype
        df_diff['source'] = my_source
        df_diff['ktype'] = self.ktype
        # 展示差集数据
        #print(df_diff)
        if df_diff.empty:
            print(f'stock_money_flow在{self.start_date.date()}到{self.end_date.date()}区间无差集数据，无需更新')
        else:
            # 有差集数据，整个df_diff表写入数据库
            df_diff.to_sql(
                name=f'stock_money_flow',
                con=self.engine,
                index=False,
                if_exists='append'
            )
            print(f"资金流向表 stock_money_flow 差集更新完成，新增数据{df_diff.shape[0]}")

        ###### 开始从stock_money_flow中获取数据，逐日计算分时资金流向
        # 取出区间内全部is_error为空的数据
        sql_flow = f"select id,code,date from stock_money_flow where source = '{my_source}' and ktype = '{self.ktype}' and date >= '{self.start_date.date()}' and date <= '{self.end_date.date()}'  and is_error is null"
        df_under_update = pd.read_sql(sql_flow , self.engine)
        if df_under_update.empty:
            print(f'stock_money_flow在{self.start_date.date()}到{self.end_date.date()}区间无待更新数据，无需计算资金流向')
            return None
        else:
            #### 获取非空数据成功，开始逐日更新
            for idx, row in df_under_update.iterrows():
                # 初始化并赋值
                m_money = money_flow()
                id = row['id']
                m_money.code = row['code']
                m_money.date = row['date']
                # 设定当天的开始和结束时间，模拟早上8点到下午16点，以获取分时数据并且兼容分时的格式
                m_money.start_date = datetime.combine(pd.to_datetime(row['date']).date(), datetime.strptime("08:00", "%H:%M").time())
                m_money.end_date = datetime.combine(pd.to_datetime(row['date']).date(), datetime.strptime("16:00", "%H:%M").time())
                m_money.ktype = self.ktype #这里ktype无需校验，如果后续逻辑拆开，分别进行插入和计算操作，则这里还需要进行校验
                # 得到非聚合的当日分时数据
                df_min = m_money.calculate_money_flow_min()
                if df_min.empty:
                    # 当日无数据
                    sql_update = f"update stock_money_flow set is_error = 1 where id = {id} "
                    print(f"资金流向表 stock_money_flow 计算完成 {m_money.code} {m_money.date} 无分时数据，无法计算资金流向 ")
                else:
                    # 有数据
                    # 计算聚合数据
                    total_money = df_min['money'].sum()
                    total_net_flow = df_min['净资金流向'].sum()
                    # 这里的波动比率是准确的。即净资金流向占总成交金额的比例
                    total_volatility  = total_net_flow/total_money if total_money != 0 else 0
                    sql_update = f"""update stock_money_flow 
                                    set volatility = {total_volatility} , 
                                    money_flow = {total_net_flow} , 
                                    is_error = 0 
                                    where id = {id}"""
                    print(f"资金流向表 stock_money_flow 计算完成 {m_money.code} {m_money.date} 资金流向 {total_net_flow} 元 波动比率 {total_volatility} ")        
                
                # 根据是否有数据，执行不同的sql_update
                # 使用事务上下文管理器，确保连接在每次执行后被正确提交并关闭，避免连接泄漏
                with self.engine.begin() as conn:
                    conn.execute(sqlalchemy.text(sql_update))

    def test_money_flow_1min(self ):
        """
        测试类函数，指定区间内单日资金流向和后续T日大盘涨跌的关联
        【逻辑】
            1. 需要做证券列表的筛选，默认需要剔除ETF和LOF类
            2. 最好可以合并加入市值类数据
            3. 列出指定日期区间所有符合条件的证券代码
            4. 列出基准指数的k线数据
            5. 证券列表中的每一个日期都对应T日基准指数的日期
            6. 列出证券区间的涨跌情况
            7. 插入基准指数在同一区间的涨跌情况
        """
        # 获取基准指数信息(akshare的指数数据也是从tspro中获取)
        



if __name__=="__main__":
    #测试资金流向
    money = money_flow()
    money.code = '688349.sh'
    money.start_date = datetime(2023,12,4)
    money.end_date = datetime.now()
    money.ktype = '1d'
    # 测试update_money_flow_min方法
    df_test = money.update_money_flow_min()
    print(df_test)
    df_1d = money.get_k_data()
    print(df_1d)
    money.ktype = '5m'
    df_result = money.calculate_money_flow_min()
    print(df_result)
