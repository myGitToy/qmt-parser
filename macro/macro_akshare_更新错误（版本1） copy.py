"""
ahkshare 更新目前存在一些错误，在5m和60m的更新过程中，如果网络连接失败，则会把上一条成功更新的数据插入到现有的证券代码中，这显然是错误的
本模块目的是从数据库中删除相关的数据，具体步骤如下：
1. 获取全部证券代码
2. 获取tspro_1d中指定时间的日线数据
3. 校验5m和60m数据的OCLV是否在1d数据的OCLV范围内
4. 如果数据不在范围内，删除5m或者60m当天的全部数据

版本1的逻辑基于未修复网络的错误，commit id b83286f04dde7c09948761c1a3ad2e879f67eb78
详见：https://huiqiao.visualstudio.com/MyFunds/_git/MyFunds/commit/b83286f04dde7c09948761c1a3ad2e879f67eb78?refName=refs%2Fheads%2Ffix-akshare_%E6%9B%B4%E6%96%B0%E6%8A%A5%E9%94%99

因此本版本会对照日线和分时线的OCLV数据进行校验，确保数据的正确性
备注：版本1未完成全部代码的编写，因为数据库已做了4.4日以后的全额删除，因此本版本已无必要
"""

import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
from apt.vendor.akshare.data import data as ak_data
from apt.vendor.tspro.security import security as ak_sec
from dotenv import load_dotenv #用于读取.env文件
class fix_akshare_update_errorV1(ak_data):
    def __init__(self):
        super().__init__()
        sec = ak_sec()
        sec.start_date = self.start_date
        sec.end_date = self.end_date
        self.df_code = sec.get_all_code()
        # 设置数据库配置
        #读取.env文件
        load_dotenv()  
        #self.engine = sqlalchemy.create_engine(os.getenv('AWS_DB_CONN'))

    pass

    def main_process(self):
        """
        主处理函数
        """
        # 获取全部证券代码
        for code in self.df_code['code']:
            # 获取日线数据
            self.code = code
            self.ktype = '1d'
            df_1d = self.get_k_data()
            print(df_1d)
            print(df_1d.dtypes)
            self.ktype = '5m'
            df_5m = self.get_k_data()
            ######## 5m数据resample到日线
            if not df_5m.empty:
                # 确保date为datetime类型并设为索引
                df_5m['date'] = pd.to_datetime(df_5m['date'])
                df_5m.set_index('date', inplace=True)
                df_5m = df_5m.resample('1D').agg({
                    'open': 'first',
                    'close': 'last',
                    'high': 'max',
                    'low': 'min'
                }).reset_index()
                df_5m['date'] = df_5m['date'].dt.date
            # 去除nan数据
            df_5m.dropna(inplace=True)
            print(df_5m)
            print(df_5m.dtypes)
            ######## 60m数据resample到日线
            self.ktype = '60m'
            df_60m = self.get_k_data()
            if not df_60m.empty:
                # 确保date为datetime类型并设为索引
                df_60m['date'] = pd.to_datetime(df_60m['date'])
                df_60m.set_index('date', inplace=True)
                df_60m = df_60m.resample('1D').agg({
                    'open': 'first',
                    'close': 'last',
                    'high': 'max',
                    'low': 'min'
                }).reset_index()
                df_60m['date'] = df_60m['date'].dt.date            
            # 去除nan数据
            df_60m.dropna(inplace=True)
            print(df_60m)
            print(df_60m.dtypes)

            # 校验5m和60m数据
            if not df_1d.empty:
                day_low = df_1d['low'].values[0]
                day_high = df_1d['high'].values[0]
                for df_min, freq in zip([df_5m, df_60m], ['5m', '60m']):
                    if not df_min.empty:
                        """
                        复杂版逻辑，检查OCLV是否在1d数据的high/low之间
                        mask = (
                            (df_min['open'] < day_low) | (df_min['open'] > day_high) |
                            (df_min['close'] < day_low) | (df_min['close'] > day_high) |
                            (df_min['high'] < day_low) | (df_min['high'] > day_high) |
                            (df_min['low'] < day_low) | (df_min['low'] > day_high)
                        )
                        """
                        # 检查5m 和60m的close数据是否在1d的相符合（简单逻辑）
                        if not ((df_min['close'] >= day_low) & (df_min['close'] <= day_high)).all():
                            print(f"{code} {freq} 存在异常close数据，建议删除该日全部数据")

            else:
                print(f"{code} 无1d数据，跳过校验")



def get_all_codes(engine):
    sql = "select distinct code from tspro_1d"
    return pd.read_sql_query(sql, engine)['code'].tolist()

def get_trade_days(engine, start_date, end_date):
    sql = f"select distinct date from tspro_1d where date between '{start_date}' and '{end_date}' order by date"
    return pd.read_sql_query(sql, engine)['date'].tolist()

def check_and_fix(engine, code, day, freq):
    # 获取1d数据
    sql_1d = f"select open, close, high, low from tspro_1d where code='{code}' and date='{day}'"
    df_1d = pd.read_sql_query(sql_1d, engine)
    if df_1d.empty:
        return
    o1, c1, h1, l1 = df_1d.iloc[0][['open', 'close', 'high', 'low']]
    # 获取5m/60m数据
    sql_min = f"select id, open, close, high, low from akshare_{freq} where code='{code}' and date(date)='{day}'"
    df_min = pd.read_sql_query(sql_min, engine)
    if df_min.empty:
        return
    # 校验
    valid = (
        (df_min['open'].between(l1, h1)) &
        (df_min['close'].between(l1, h1)) &
        (df_min['high'].between(l1, h1)) &
        (df_min['low'].between(l1, h1))
    ).all()
    if not valid:
        # 删除当天全部数据
        with engine.begin() as conn:
            conn.execute(text(f"delete from akshare_{freq} where code='{code}' and date(date)='{day}'"))
        print(f"{code} {day} {freq} 存在异常，已删除该日全部数据")

    def main(start_date, end_date):
        codes = get_all_codes(engine)
        days = get_trade_days(engine, start_date, end_date)
        for code in codes:
            for day in days:
                for freq in ['5m', '60m']:
                    check_and_fix(engine, code, day, freq)

if __name__ == "__main__":
    # 初始化
    ak_fix_process = fix_akshare_update_errorV1()
    # 设置需要检查的日期区间
    ak_fix_process.start_date = datetime(2025, 1, 1, 8) # 起始日期
    ak_fix_process.end_date = datetime(2025, 1, 8,18)# 结束日期
    print(ak_fix_process.df_code)
    ak_fix_process.main_process()
