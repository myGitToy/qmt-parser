import pymysql
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
from datetime import datetime
from apt.vendor.tspro.security import security as security
import os
from urllib.parse import urlparse
from tqdm import tqdm

# 显示全部的列
pd.set_option('display.max_columns', None)

class DatabaseSync:
    """
    数据库同步类
    需要加载两个mysql数据库，其中engine_A是主数据库，engine_B是次要数据库
    """
    def __init__(self, 
                 datatable_name, code=None , 
                 start_date=None, end_date=None , 
                 dual_sync = True , 
                 engine_A = "UBUNTU186_DB_CONN" ,
                 engine_B = "LOCAL_DB_CONN"):
        """
        初始化同步类
        :param datatable_name: 数据表名称
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param code: 证券代码
        :param dual_sync: 是否双向同步，默认为True ; False表示只从A(主数据库)同步到B（次要数据库）
        :param engine_A: 主数据库连接字符串
        :param engine_B: 次要数据库连接字符串       
        """
        self.datatable_name = datatable_name
        self.start_date = start_date
        self.end_date = end_date
        self.code = code
        self.dual_sync = dual_sync

        # 检查数据表名称
        if self.datatable_name not in ['tspro_1d', 'tspro_1m','tspro_5m', 'tspro_30m', 'tspro_60m', 'akshare_1m', 'akshare_5m', 'akshare_60m']:
            raise ValueError("Invalid datatable name. Supported values are: tspro_1d, tspro_5m, tspro_30m, tspro_60m, akshare_1m, akshare_60m")
        
        # 加载 .env 文件
        load_dotenv()

        # 从 .env 文件中读取数据库连接字符串
        self._A_CONN_STR = os.getenv(engine_A)
        self._B_CONN_STR = os.getenv(engine_B)
        # 创建 SQLAlchemy 引擎
        try:
            self.engine_A = create_engine(self._A_CONN_STR)
            self.engine_B = create_engine(self._B_CONN_STR)
        except Exception as e:
            raise ConnectionError(f"连接数据库发生错误，请检查字符串或网络连接 {e}")

    def _sum_total_data(self) -> bool:
        """
        统计两个数据库中数据的总量
        :param datatable_name（使用init初始化参数）: 数据表名称
        :param start_date（使用init初始化参数）: 开始日期
        :param end_date（使用init初始化参数）: 结束日期
        :param code（使用init初始化参数）: 证券代码
        返回 True：表示数据量相等，False 表示数据量不相等
        """
        query_A = f"SELECT DATE(date), COUNT(date) AS sum_total FROM {self.datatable_name} WHERE date BETWEEN '{self.start_date}' AND '{self.end_date}' AND code = '{self.code}' GROUP BY DATE(date) ORDER BY DATE(date)"
        query_B = f"SELECT DATE(date), COUNT(date) AS sum_total FROM {self.datatable_name} WHERE date BETWEEN '{self.start_date}' AND '{self.end_date}' AND code = '{self.code}' GROUP BY DATE(date) ORDER BY DATE(date)"
        # 修复两个空表合并后报告future warning  
        df_A = pd.DataFrame()
        df_B = pd.DataFrame()       
        df_A = pd.read_sql_query(query_A, self.engine_A)
        df_B = pd.read_sql_query(query_B, self.engine_B)
        return df_A['sum_total'].sum() == df_B['sum_total'].sum()

    def sync(self):
        """
        同步两个数据库中的日线或者分钟线数据
        """
        if self.code is None:
            sec = security()
            sec.start_date = self.start_date
            sec.end_date = self.end_date
            df_code = sec.get_all_code()
            print(f"查询到的证券代码数量: {len(df_code)}")
            if df_code.empty:
                print(f"没有找到符合条件的证券代码，请检查日期")
                return
            code_list = df_code['code'].tolist()
        else:
            code_list = [self.code] if isinstance(self.code, str) else self.code

        for code in tqdm(code_list, desc="同步进度", unit="证券代码"):
            if isinstance(code, str):
                self.code = code.strip()
            if not self.code:
                print(f"证券代码 {self.code} 无效，跳过该证券")
                continue
            if self._sum_total_data():
                print(f"{self.datatable_name}:{self.code} 数据量相等，无需同步。")
            else:
                df_A = pd.DataFrame()
                df_B = pd.DataFrame() 
                query_A = f"SELECT code,date,open,high,low,close,volume,money FROM {self.datatable_name} WHERE code ='{self.code}' AND date >= '{self.start_date}' AND date <= '{self.end_date}'"
                query_B = f"SELECT code,date,open,high,low,close,volume,money FROM {self.datatable_name} WHERE code ='{self.code}' AND date >= '{self.start_date}' AND date <= '{self.end_date}'"
                df_A = pd.read_sql_query(query_A, self.engine_A)
                df_B = pd.read_sql_query(query_B, self.engine_B)

                ######## 1. 主要同步方向 ########
                df_diff_AtoB = df_A.copy()
                df_diff_AtoB = pd.concat([df_A , df_B , df_B ]).drop_duplicates(subset = ['code','date'] , keep = False)
                #print(df_A)
                #print(df_B)
                
                if not df_diff_AtoB.empty:
                    df_diff_AtoB.to_sql(self.datatable_name, self.engine_B, if_exists='append', index=False)
                    print(f"{self.datatable_name}:{self.code} 已将 {len(df_diff_AtoB)} 行数据从 A 同步到 B.")
                else:
                    print(f"{self.datatable_name}:{self.code} A->B 没有需要同步的数据.")
            
                ######## 2. 次要同步方向 ########

                if self.dual_sync == True:
                    df_diff_BtoA = df_B.copy()
                    df_diff_BtoA = pd.concat([df_B , df_A , df_A ]).drop_duplicates(subset = ['code','date'] , keep = False)
                    if not df_diff_BtoA.empty:
                        df_diff_BtoA.to_sql(self.datatable_name, self.engine_A, if_exists='append', index=False)
                        print(f"{self.datatable_name}:{self.code} 已将 {len(df_diff_BtoA)} 行数据从 B 同步到 A.")
                    else:
                        print(f"{self.datatable_name}:{self.code} B->A 没有需要同步的数据.")
        self.engine_A.dispose()
        self.engine_B.dispose()


if __name__ == "__main__":
    start_date = datetime(2025, 4, 1)
    end_date = datetime(2025, 8, 16)
    code = None
    datatable_name = 'akshare_1m'
    dual_sync = True
    syncer = DatabaseSync(datatable_name=datatable_name, 
                          start_date=start_date, end_date=end_date, 
                          code=code, dual_sync=False,
                          )#engine_B="docker_201_DB_CONN",
    syncer.sync()

