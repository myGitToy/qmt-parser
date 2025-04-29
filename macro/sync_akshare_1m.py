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
# 加载 .env 文件
load_dotenv()

# 从 .env 文件中读取数据库连接字符串
A_CONN_STR = os.getenv("LOCAL_DB_CONN")
B_CONN_STR = os.getenv("UBUNTU186_DB_CONN")

def get_mysql_connection(conn_str):
    # 使用 urlparse 解析连接字符串
    parsed = urlparse(conn_str)

    return pymysql.connect(
        host=parsed.hostname,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path.lstrip("/"),
        port=parsed.port
    )
def _sum_total_data(datatable_name="akshare_1m", code=None, start_date=None, end_date=None,engine_A=None, engine_B=None):
    """    
    统计两个数据库中数据的总量
    返回 true：表示数据量相等，false表示数据量不相等
    """
    df_A = pd.DataFrame()
    df_B = pd.DataFrame() 
    query_A = f"select date(date), count(date) as sum_total from {datatable_name} where date between '{start_date}' and '{end_date}' and code = '{code}' GROUP BY date(date) order by date(date)"
    query_B = f"select date(date), count(date) as sum_total from {datatable_name} where date between '{start_date}' and '{end_date}' and code = '{code}' GROUP BY date(date) order by date(date)"
    df_A = pd.read_sql_query(query_A, engine_A)
    df_B = pd.read_sql_query(query_B, engine_B)
    # 如果两张表sum_total累加相等，返回True，否则返回False
    return df_A['sum_total'].sum() == df_B['sum_total'].sum() 


def sync_stock_data(datatable_name="akshare_1m", code=None, start_date=None, end_date=None): 
    """
    同步两个数据库中的日线或者分钟线数据
    :param datatable_name: 数据表名称，目前仅接受tspro_1d,tspro_5m,tspro_30m,tspro_60m,akshare_1m,akshare_60m
    :param code: 证券代码，默认为None表示所有代码
    :param start_date: 开始日期，默认为None表示不限制开始日期
    :param end_date: 结束日期，默认为None表示不限制结束日期
    """
    # 检查数据表名称
    if datatable_name not in ['tspro_1d', 'tspro_5m', 'tspro_30m', 'tspro_60m', 'akshare_1m', 'akshare_5m','akshare_60m']:
        raise ValueError("Invalid datatable name. Supported values are: tspro_1d, tspro_5m, tspro_30m, tspro_60m, akshare_1m, akshare_60m")
    
    # 创建 SQLAlchemy 引擎
    try:
        engine_A = create_engine(A_CONN_STR)
        engine_B = create_engine(B_CONN_STR)
    except Exception as e:
        print(f"连接数据库发生错误，请检查字符串或网络连接 {e}")
        return

    if code == None:
        # 证券列表为空，查询所有的证券代码
        sec = security()
        sec.start_date = start_date
        sec.end_date = end_date
        df_code = sec.get_all_code()
        print(f"查询到的证券代码数量: {len(df_code)}")
        # 下面两条被注释，查询时为全表查询，如果对1m表进行查询，耗时太长
        #sql_query_code = f"select distinct code from {datatable_name} where date >= '{start_date}' and date <= '{end_date}'"
        #df_code = pd.read_sql_query(sql_query_code, engine_B)
        if df_code.empty:
            print(f"没有找到符合条件的证券代码，请检查日期")
            return
        code_list = df_code['code'].tolist()
    else:
        # 证券列表不为空，查询指定的证券代码
        code_list = [code] if isinstance(code, str) else code
    # 数据校验，展示code_list
    #print(f"待同步的证券代码列表: {code_list}")

    ###### 数据处理环节 ######
    # 使用 tqdm 增加进度条提示
    for code in tqdm(code_list, desc="同步进度", unit="证券代码"):
        if isinstance(code, str):
            code = code.strip()
        if not code:
            print(f"证券代码 {code} 无效，跳过该证券")
            continue
        # 检查AB两张表数据是否相等     
        if _sum_total_data(datatable_name = datatable_name, code = code, start_date = start_date, end_date = end_date, engine_A = engine_A, engine_B = engine_B):
            print(f"{datatable_name}:{code} 数据量相等，无需同步。")
        else:
            # 数据不同，进行差异更新  
            df_A = pd.DataFrame()
            df_B = pd.DataFrame() 
            query_A = f"SELECT code,date,open,high,low,close,volume,money FROM {datatable_name} WHERE code ='{code}' AND date >= '{start_date}' AND date <= '{end_date}'"
            query_B = f"SELECT code,date,open,high,low,close,volume,money FROM {datatable_name} WHERE code ='{code}' AND date >= '{start_date}' AND date <= '{end_date}'"
            df_A = pd.read_sql_query(query_A, engine_A)
            df_B = pd.read_sql_query(query_B, engine_B)
            # 数据格式调整（暂时没有代码，理论上两边数据库取出来的格式应该保持一致的）
            # 数据校验
            #print(df_A)
            """
            同步系统的说明
            这里可以进行双向同步
            1. 主要同步方向：B中有，A中没有的数据
                同步方向：B向A同步，即将B中有而A中没有的数据插入到A中
            2. 次要同步方向：A中有，B中没有的数据
                同步方向：A向B同步，即将A中有而B中没有的数据插入到B中
            """
            ######## 1. 主要同步方向 ########
            # 找出 B 中有但 A 中没有的数据，使用差集操作
            df_diff_BtoA = df_B.copy()
            df_diff_BtoA = pd.concat([df_B , df_A , df_A ]).drop_duplicates(subset = ['code','date'] , keep = False)
            #print(f"{code} 差异数据[A+B合集再-A]（B独有数据）:\n{df_diff_BtoA}")
            # 如果有差异数据，将其插入到 A 数据库
            if not df_diff_BtoA.empty:
                # 同步操作，模拟同步时请注释掉
                df_diff_BtoA.to_sql(datatable_name, engine_A, if_exists='append', index=False)
                print(f"{datatable_name}:{code} 已将 {len(df_diff_BtoA)} 行数据从 B 同步到 A.")
            else:
                print(f"{datatable_name}:{code} B->A 没有需要同步的数据。")
                

            ######## 2. 次要同步方向 ########
            # 找出 A 中有但 B 中没有的数据
            df_diff_AtoB = df_A.copy()
            df_diff_AtoB = pd.concat([df_A , df_B , df_B ]).drop_duplicates(subset = ['code','date'] , keep = False)
            #print(f"{code} 差异数据[A+B合集再-B]（A独有数据）:\n{df_diff_AtoB}")
            # 打印差异数据
        # print(f"{code} 差异数据（A有但B没有）:\n{df_diff_AtoB}")
            # 如果有差异数据，将其插入到 B 数据库
            if not df_diff_AtoB.empty:
                # 同步操作，模拟同步时请注释掉
                df_diff_AtoB.to_sql(datatable_name, engine_B, if_exists='append', index=False)
                print(f"{datatable_name}:{code} 已将 {len(df_diff_AtoB)} 行数据从 A 同步到 B.")
            else:
                print(f"{datatable_name}:{code} A->B 没有需要同步的数据。")
            # 关闭数据库连接
            engine_A.dispose()
            engine_B.dispose()
            # 增加进度条提示


if __name__ == "__main__":
    start_date = datetime(2025, 4, 1)
    end_date = datetime(2025, 4,28)
    code = '600038.SH'
    datatable_name = 'akshare_1m'
    sync_stock_data(datatable_name = datatable_name, start_date = start_date, end_date = end_date)
