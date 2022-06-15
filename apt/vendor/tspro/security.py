import numpy as np
import pandas as pd
import tushare as ts
import sqlalchemy
from datetime import datetime
from apt.vendor.tspro.base import base as base
from apt.vendor.tspro.base import stock as stock
from sqlalchemy.types import NVARCHAR , Float, Integer , Date

class security(base , stock):
    """
    专门处理security的类
    包含交易日历 交易列表
    """
    def daily_update(self , type = ['stock','index','fund','etf','lof','fja','fjb']):
        """
        security日常更新
        type 证券类型，支持多选 默认为全部（目前不包含期货）
        """
        #打印标题
        print("############正在准备更新security证券代码信息###########")
        df_security = get_all_securities(type)
        #将code的索引转换成列
        df_security.reset_index(level = 0 , inplace = True)
        #重命名为code
        df_security.rename(columns = {'index':'code'} , inplace = True)
        #print(df_security)
        #dataframe列名的数据类型进行映射
        dtypedict = {
            'code': NVARCHAR(length = 24),
            'display_name': NVARCHAR(length = 128),
            'name': NVARCHAR(length = 128),
            'start_date': Date(),
            'end_date': Date(),
            'type': NVARCHAR(length = 8)
                    }
        #数据保存至数据库
        if df_security.empty == True:
            print("原始数据为空，无法导入数据库")
        else:
            df_security.to_sql(
                    name = 'jqdata_security',
                    con = self.engine,
                    index = False,
                    if_exists = 'replace',
                    index_label='code' , #设置主键(设置未成功)
                    dtype=dtypedict) #映射列的数据类型

            with self.engine.connect() as con:
                #设置主键
                con.execute('ALTER TABLE `jqdata_security` ADD PRIMARY KEY (`code`);')
                #设置索引（其实主键和索引一致的话，是可以不需要设置索引的）
                #con.execute('CREATE INDEX index `jqdata_security` (`code`);')
            print("数据已上传完成(security)")

    def get_security(self , code = None , day = datetime.now()):
        """
        获取单代码的security信息（需要满足）
        【输入】
            code 证券代码 默认为空
        【输出】
            dataframe:code|display_name|name|start_date|end_date|type|valid
        """
        if code != None:
            #脱机查询
            #定位数据库中的最后日期(这里默认使用510300进行查询)
            df = pd.read_sql_query(f"select * from jqdata_security where code = '{code}' and start_date<='{day.date()}' and end_date >='{day.date()}'" , self.engine)
            if df.empty == True:
                #数据库不存在数据
                return pd.DataFrame()
            else:
                #数据库存在数据，返回
                return df
        else:
            raise ValueError(f'证券代码不能为空，请检查')


    def daily_update_money_flow(self , code_list =  None , start_date = datetime(2005,1,1) , end_date = datetime.now()):
        """
        每日资金流向更新
        """
        #获取更新列表
        if code_list == None:
            #更新列表未填写，则默认为空，即全部更新
            code_list = list(get_all_securities(['stock'],date = end_date).index)
        #打印标题
        print("############正在准备更新资金流向信息###########")
        """
        更新逻辑：
            1. 取出所有的stock列表，进行单代码循环
            2. 取出该代码在数据库中，指定日期间的最后更新日期
                2.1 为空，则全部更新
                2.2 不为空，则取出最后日期，以这个日期为基准，进行更新
            3. 数据写入数据库
        逻辑优点和不足：
            1. 单循环运行效率较高
            2. 可以解决日常更新中，有部分日期重复的问题，比如每月的更新开始周期设定为1号，但5号更新是会自动过滤1-4号的数据
            3. 上述第二条还有一个很重要的应用场景：因为是指定区间的更新取最后一天，因此如果先更新了2020年的数据，随后再要更新2019年的数据，
                在这种情况下也是可以的，因为取的是区间最后一天，因此2019全年的数据也是空，也就会全部读取和更新
            4. 这里写入时没有做去重，可能还是会触发唯一性约束错误（可能性低于0.01%）
        """
        for code in code_list:
            #获取数据库中存在的数据最后更新日期（加入强制使用索引的内容）
            query2 = f"select date FROM jqdata_money_flow FORCE INDEX (main) WHERE date BETWEEN '{start_date.date()}' and '{end_date.date()}' and code = '{code}' ORDER BY date DESC LIMIT 1" 
            df_db = pd.read_sql_query(query2 , self.engine)
            if df_db.empty == True:
                #数据库不存在数据
                new_start_date = start_date
            else:
                #数据库存在数据，新定义开始日期（数据库最后一天+1）
                new_start_date =  df_db.loc[0 , 'date']  + datetime.timedelta(days=1)         
            df_flow = get_money_flow(security_list = code , start_date = new_start_date, end_date = end_date)
            #重命名列（money_flow中的证券代码sec_code和数据库中的不一致）
            df_flow.rename(columns = {'sec_code':'code'} , inplace = True)
            #print(df_flow)
            #保存至数据库 
            if df_flow.empty == True:
                print(f"{code}数据为空，跳过上传")
            else:
                df_flow.to_sql(
                        name = 'jqdata_money_flow',
                        con = self.engine,
                        index = False,
                        if_exists = 'append')
                print("%s 数据已上传完成(money flow)" % (code))

    def get_calendar(self , exchange = 'SSE' , is_open = 1 ):
        """
        获取交易日历
        输入：
            exchange：交易所代码 默认全部使用上交所信息 SSE上交所 SZSE深交所
            is_open：获取交易日的类型 默认剔除非交易日
        输出：
            date 交易日期
            is_open 交易日的类型
        """
        query = f"select date,is_open FROM tspro_calendar WHERE exchange = '{exchange}' and is_open = {is_open} and date BETWEEN '{self.start_date.date()}' and '{self.end_date.date()}'" 
        df_db = pd.read_sql_query(query , self.engine)
        if df_db.empty == True:
            #数据库不存在数据
            return pd.DataFrame()
        else:
            #数据库存在数据
            return df_db
                
if __name__=="__main__":
    #测试交易日历功能
    a = base()
    sec = security()
    a.start_date = datetime(2022,1,1)
    a.end_date = datetime(2022,9,1)
    df = a.pro.trade_cal(exchange='SZSE', start_date='20180101', end_date='20181231')
    print(df)
    #测试交易日历读取功能
    df_read = sec.get_calendar()

    