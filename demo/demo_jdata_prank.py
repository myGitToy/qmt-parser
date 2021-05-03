import numpy as np
import pandas as pd
import tushare as ts
import sqlalchemy
import datetime
from jqdatasdk import *
from apt.vendor.jqdata.base import base as base
from apt.vendor.jqdata.jqdata import data as jqdata
from apt.vendor.jqdata.ETF import ETF as ETF


jq = jqdata(rds_host = jqdata.数据源.localhost , myauth = True )
code_list = ['512980','002746','002446','600075','000058','510300','510500','510050','510180','510900','159920','518880','159928','515030','512580','512170','512290','515220','515210','512720','515880','159995','159939','512760','512800','512880','512660','511010','511260','159949','512200','600089','600036','600519','600570','600958','300033','512200','300059','300236','603976','000651','601318','000063','159996','000001','600371','002041','688002','688005','688007','688008','688009','688012','688033','688088','688122','688099','688321','603187','159967']
#代码转换
code_list = normalize_code(code_list)
start = datetime.datetime(2020,10,1)
end = datetime.datetime.now()
df_main = pd.DataFrame()


for code in code_list:

    df = jq.get_k_data(code = code , start_date = start , end_date = end , ktype = '60m' ,fq =base.复权.动态复权)
    df['p40'] = df['close'].rolling(100).quantile(0.40)
    df['p50'] = df['close'].rolling(100).quantile(0.50)
    df['p60'] = df['close'].rolling(100).quantile(0.60)
    df['p75'] = df['close'].rolling(100).quantile(0.75)
    df['p85'] = df['close'].rolling(100).quantile(0.85)
    df['p90'] = df['close'].rolling(100).quantile(0.90)
    df['p95'] = df['close'].rolling(100).quantile(0.95)
    df['code'] = code
    df_main = pd.concat([df_main, df],sort = False)
df_main [['date','code','open','high','low','close','p40','p50','p60','p75','p85','p90','p95']].to_csv('.\\data\\quantile.csv' , encoding = 'utf_8_sig')


