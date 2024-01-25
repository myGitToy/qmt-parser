import pandas as pd
import numpy as np
import json
from pymysql.converters import escape_string   # escape_string函数用来转义json类型数据
from datetime import datetime,timedelta
from apt.vendor.tspro.data import data as ts_data
from datetime import datetime
from sqlalchemy import create_engine,exc,delete,text   #用来捕捉sqlalchemy的异常

class cum_turnover(ts_data):
    """
    全换手区间每日存盘、计算、应用类
    """
    def __init__(self):
        #初始化父类
        super().__init__()
    def update_cumulative_turnover(self):
        """
        更新累计换手率入库（刚移植，未测试）
        """
        df_basic = pd.read_sql_query(f"select code,date from tspro_basic force index (date) where date between '{self.start_date.date()}' and '{self.end_date.date()}'" , self.engine)
        df_cumulative_turnover = pd.read_sql_query(f"select code,date from tspro_cumulative_turnover force index (date) where date between '{self.start_date.date()}' and '{self.end_date.date()}'" , self.engine)
        df_db = pd.concat([df_basic, df_cumulative_turnover]).drop_duplicates(subset=['code','date'], keep=False)
        # Get rows from df_basic that are not in df_cumulative_turnover
        #df_missing_rows = df_basic[~df_basic[['code', 'date']].isin(df_cumulative_turnover[['code', 'date']])].dropna()
        #保存至数据库
        if df_db.empty == True:
            print("差集为空，跳过写入数据库")
        else:
            df_db.to_sql(
                    name = f'tspro_cumulative_turnover',
                    con = self.engine,
                    index = False,
                    if_exists = 'append')
            print(f"数据上传完成(tspro_cumulative_turnover)|新增数据{df_db.shape[0]}")
    
    def __sql_execute_time(self , sql):
        """
        执行SQL语句（刚移植，未测试）
        """
        # 记录开始时间
        start_time = datetime.now()

        # 执行SQL语句
        df = pd.read_sql_query(sql , self.engine)
        # 记录结束时间
        end_time = datetime.now()
        # 计算并打印执行时间
        execution_time = end_time - start_time
        print(f"SQL execution time: {execution_time}")
        return df

    def analyse_cumulative_turnover(self):
        """
        更新和分析累计换手率（刚移植，未测试）
        目前需要更新turnover_date,turnover_date_f,turnover_days,turnover_days_f这四个字段
        """
        sql_basic = f"select code,date,turnover_rate,turnover_rate_f from tspro_basic FORCE INDEX(date) where date between '{self.start_date.date()}' and '{self.end_date.date()}'"
        print(sql_basic)
        df_basic = self.__sql_execute_time(sql_basic)
        df_cumulative_turnover = self.__sql_execute_time(f"select code,date,turnover_valid from tspro_cumulative_turnover FORCE INDEX(date) where date between '{self.start_date.date()}' and '{self.end_date.date()}'" )
        #df_cumulative_turnover = pd.read_sql_query(f"select code,date,turnover_valid from tspro_cumulative_turnover force index(date) where date between '{self.start_date.date()}' and '{self.end_date.date()}'" , self.engine)
        df_cum_na = df_cumulative_turnover[df_cumulative_turnover['turnover_valid'].isnull()]
        #历遍df_cum_na
        for index , row in df_cum_na.iterrows():
            code = row['code']
            e_date = row['date']
            for n in [100,300,500,1000,5000]:
                s_date = e_date - timedelta(days = n)
                #df_db为tspro_basic数据查询中以e_date为基准的数据，降序排列
                df_db = pd.read_sql_query(f"select code,date,turnover_rate,turnover_rate_f from tspro_basic where code = '{code}' and date between '{s_date}' and '{e_date}'" , self.engine).sort_values('date', ascending=False)
                #数据条目的最后一个日期，用来进行比较
                last_date = df_db.iloc[-1]['date']
                #计算换手率累计值
                df_db['cum_turnover'] = df_db['turnover_rate'].cumsum()
                df_db['cum_turnover_f'] = df_db['turnover_rate_f'].cumsum()
                #需要df_db累加后的turnover_rate和turnover_rate_f均大于100                
                if df_db.query('cum_turnover >= 100').empty == False and df_db.query('cum_turnover_f >= 100').empty == False:
                    #累加值超过100，数据有效
                    turnover_date = df_db[df_db['cum_turnover'] >= 100].iloc[0]['date']
                    turnover_date_f = df_db[df_db['cum_turnover_f'] >= 100].iloc[0]['date']
                    turnover_days = df_db.query('cum_turnover <= 100').shape[0]
                    turnover_days_f = df_db.query('cum_turnover_f <= 100').shape[0]
                    bit = 1
                    #检查100%换手率的数据
                    #print(df_db.query('cum_turnover <= 100'))
                    print(f"{code}|{e_date}前数{n}日数据有效，对应换手日期{turnover_date}|{turnover_date_f}；交易日{turnover_days}|{turnover_days_f}")
                    #更新数据库
                    sql_update = text(f"update tspro_cumulative_turnover set turnover_date = '{turnover_date}' , turnover_date_f = '{turnover_date_f}' , turnover_days = {turnover_days} , turnover_days_f = {turnover_days_f} , turnover_valid = {bit} where code = '{code}' and date = '{e_date}'")
                    try:
                        with self.engine.begin() as connection:
                            connection.execute(sql_update)
                    except exc.ResourceClosedError:
                        print(f"更新{code}|{e_date}序列失败！")                    
                    #数据有效，跳出for循环
                    break
                else:
                    #累加值未超过100，数据无效
                    print(f"{code}前数{n}日数据无效，继续增加天数")
                    turnover_date = None
                    turnover_date_f = None
                    #这里还有一种情况，就是for列表循环完毕，数据依旧无效
                    if n == 5000:
                        print(f"未找到100%换手数据，可能数据无效也可能是新股、次新股")
                        bit = 0
                        sql_update = text(f"update tspro_cumulative_turnover set turnover_valid = {bit}  where code = '{code}' and date = '{e_date}'")
                        try:
                            with self.engine.begin() as connection:
                                connection.execute(sql_update)
                        except exc.ResourceClosedError:
                            print(f"更新{code}|{e_date}序列失败！")                             
                        #raise ValueError(f"{code}前数{n}日数据无效，程序终止")
    
    def update_price_range_1d(self):
        """
        更新基于tspro日线数据的全换手区间信息(全代码) JSON格式
        目前需要更新price_range_1d,price_range_1d_f这两个字段
        【输入】继承自父类的属性
            start_date：开始日期
            end_date：结束日期
        
        """
        #第一步检查turnover_valid为null的数量
        sql_null = f"SELECT * FROM stock.tspro_cumulative_turnover WHERE date(date) between '{self.start_date.date()}' and '{self.end_date.date()}' and turnover_valid is null"
        db_null = pd.read_sql(sql_null , self.engine)   
        if db_null.empty == False:
            print(f"存在{db_null.shape[0]}条turnover_valid为null的数据，需要更新")
            #第二步更新turnover_valid为null的数据
            self.analyse_cumulative_turnover()
        #第二步取出price_valid_1d为null的数据
        sql_null = f"SELECT code,date,turnover_valid,turnover_date,turnover_date_f,turnover_days,turnover_days_f FROM stock.tspro_cumulative_turnover WHERE date(date) between '{self.start_date.date()}' and '{self.end_date.date()}' and price_valid_1d is null"
        price_null = pd.read_sql(sql_null , self.engine)
        if price_null.empty == False:
            print(f"存在{price_null.shape[0]}条price_valid_1d为null的数据，需要更新")
            #第三步更新price_valid_1d为null的数据
            for index , row in price_null.iterrows():
                day = row['date']
                code = row['code']
                price_range_1d = self.__lambda_price_range_1d(row , k_type = '1d')
                price_range_1d_f = self.__lambda_price_range_1d_f(row , k_type = '1d')
                # 将 Python 对象转换为 JSON 格式的字符串
                price_range_1d_json = json.dumps(price_range_1d, ensure_ascii=False)
                price_range_1d_f_json = json.dumps(price_range_1d_f, ensure_ascii=False)
  
                #print(price_range_1d)  
                #print(self.__lambda_is_json(price_range_1d))  
                #启用事务更新，写回数据库  
                 
                sql_update = text(f"""
                update tspro_cumulative_turnover 
                set price_range_1d = :price_range_1d, 
                    price_range_1d_f = :price_range_1d_f,
                    price_valid_1d = 1 
                where code = :code and date = :day""")    
                #sql_update = sql_update.format(json1=escape_string(d_params), json2=escape_string(d_params)) 
                try:
                    with self.engine.begin() as connection:
                        connection.execute(sql_update, {"price_range_1d": price_range_1d_json, "price_range_1d_f": price_range_1d_f_json, "code": row['code'], "day": row['date']})
                        print(f"更新{row['code']}|{row['date']}序列成功！")
                except exc.ResourceClosedError:
                    print(f"更新{row['code']}|{row['date']}序列失败！")
        else:
            print(f"不存在price_valid_1d为null的数据，跳过更新")  

    def update_price_range_1d_by_code(self):
        """
        更新基于tspro日线数据的全换手区间信息(指定代码) JSON格式
        目前需要更新price_range_1d,price_range_1d_f这两个字段
        【输入】继承自父类的属性
            code：证券代码
            start_date：开始日期
            end_date：结束日期
        
        """
        #第一步检查turnover_valid为null的数量
        sql_null = f"SELECT * FROM stock.tspro_cumulative_turnover WHERE date(date) between '{self.start_date.date()}' and '{self.end_date.date()}' and code = '{self.code}' and turnover_valid is null"
        db_null = pd.read_sql(sql_null , self.engine)   
        if db_null.empty == False:
            print(f"存在{db_null.shape[0]}条turnover_valid为null的数据，需要更新")
            #第二步更新turnover_valid为null的数据
            self.analyse_cumulative_turnover()
        #第二步取出price_valid_1d为null的数据
        sql_null = f"SELECT code,date,turnover_valid,turnover_date,turnover_date_f,turnover_days,turnover_days_f FROM stock.tspro_cumulative_turnover WHERE date(date) between '{self.start_date.date()}' and '{self.end_date.date()}' and code = '{self.code}' and price_valid_1d is null"
        price_null = pd.read_sql(sql_null , self.engine)
        if price_null.empty == False:
            print(f"存在{price_null.shape[0]}条price_valid_1d为null的数据，需要更新")
            #第三步更新price_valid_1d为null的数据
            for index , row in price_null.iterrows():
                day = row['date']
                code = row['code']
                price_range_1d = self.__lambda_price_range_1d(row , k_type = '1d')
                price_range_1d_f = self.__lambda_price_range_1d_f(row , k_type = '1d')
                # 将 Python 对象转换为 JSON 格式的字符串
                price_range_1d_json = json.dumps(price_range_1d, ensure_ascii=False)
                price_range_1d_f_json = json.dumps(price_range_1d_f, ensure_ascii=False)
  
                #print(price_range_1d)  
                #print(self.__lambda_is_json(price_range_1d))  
                #启用事务更新，写回数据库  
                 
                sql_update = text(f"""
                update tspro_cumulative_turnover 
                set price_range_1d = :price_range_1d, 
                    price_range_1d_f = :price_range_1d_f,
                    price_valid_1d = 1 
                where code = :code and date = :day""")    
                #sql_update = sql_update.format(json1=escape_string(d_params), json2=escape_string(d_params)) 
                try:
                    with self.engine.begin() as connection:
                        connection.execute(sql_update, {"price_range_1d": price_range_1d_json, "price_range_1d_f": price_range_1d_f_json, "code": row['code'], "day": row['date']})
                        print(f"更新{row['code']}|{row['date']}序列成功！")
                except exc.ResourceClosedError:
                    print(f"更新{row['code']}|{row['date']}序列失败！")
        else:
            print(f"不存在price_valid_1d为null的数据，跳过更新")

    def __lambda_is_json(self , myjson):
        """
        内部函数，用来判断一个字符串是否是JSON值
        """
        try:
            json_object = json.loads(myjson)
        except ValueError as e:
            return False
        return True
    
    def __lambda_price_range_1d(self , row , k_type = '1d') -> dict:
        """
        全换手区间价格分布 每0.05为一个分位数
        【输入】
            row：数据行（tspro_cumulative_turnover） 必须包含的列：code,date,turnover_date
            k_type：K线类型 默认为1d  
        【返回】
            JSON值 分位数分布
        """
        tspro = ts_data()
        tspro.code = row['code']
        tspro.start_date = pd.to_datetime(row['turnover_date']) + timedelta(hours=8)
        tspro.end_date = pd.to_datetime(row['date']) + timedelta(hours=16)
        tspro.ktype = k_type
        df = tspro.get_k_data()
        if df.empty:
            raise ValueError('没有数据')
        #取得区间内的加权平均价格分布
        # 按收盘价分组，计算每个价格的总成交量
        volume_by_price = df.groupby('close')['volume'].sum()
        # 计算累计成交量百分比
        volume_by_price = volume_by_price.sort_index()
        cumulative_volume_pct = volume_by_price.cumsum() / volume_by_price.sum()
        # 找出每5%分位数对应的价格
        quantiles = np.round(np.arange(0.05, 1.05, 0.05), 2)
        prices_at_quantiles = cumulative_volume_pct.index[cumulative_volume_pct.searchsorted(quantiles)]    
        # 四舍五入到小数点后两位
        prices_at_quantiles = prices_at_quantiles.round(2)
        # 输出JSON
        #output = pd.Series(prices_at_quantiles, index=quantiles).to_json()     
        output = pd.Series(prices_at_quantiles, index=quantiles)
        # 输出dict格式
        return output.to_dict()
    
    def __lambda_price_range_1d_f(self , row , k_type = '1d')  -> dict:
        """
        全换手区间价格分布 每0.05为一个分位数
        【输入】
            row：数据行（tspro_cumulative_turnover） 必须包含的列：code,date,turnover_date_f
            k_type：K线类型 默认为1d  
        【返回】
            JSON值 分位数分布
        """
        tspro = ts_data()
        tspro.code = row['code']
        tspro.start_date = pd.to_datetime(row['turnover_date_f']) + timedelta(hours=8)
        tspro.end_date = pd.to_datetime(row['date']) + timedelta(hours=16)
        tspro.ktype = k_type
        df = tspro.get_k_data()
        if df.empty:
            raise ValueError('没有数据')
        #取得区间内的加权平均价格分布
        # 按收盘价分组，计算每个价格的总成交量
        volume_by_price = df.groupby('close')['volume'].sum()
        # 计算累计成交量百分比
        volume_by_price = volume_by_price.sort_index()
        cumulative_volume_pct = volume_by_price.cumsum() / volume_by_price.sum()
        # 找出每5%分位数对应的价格
        quantiles = np.round(np.arange(0.05, 1.05, 0.05), 2)
        prices_at_quantiles = cumulative_volume_pct.index[cumulative_volume_pct.searchsorted(quantiles)]    
        # 四舍五入到小数点后两位
        prices_at_quantiles = prices_at_quantiles.round(2)
        # 输出JSON
        output = pd.Series(prices_at_quantiles, index=quantiles)
        return output.to_dict()

    def __lambda_K线校验(row, k_type = '1m'):
        """
        对cumulative_turnover数据进行K线校验，返回区间内的K线数量
        【输入】
            row：数据行 必须包含的列：code,start_date,end_date
            k_type：K线类型 默认为1m
        """
        ak = ak_data()
        ak.code = row['code']
        #这边对开始时间和结束时间进行校验，取日期+8小时/日期+16小时
        #备注：按照cumulative_turnover的数据，开始时间结束时间都是日期类函数，理论上不需要进行校验，这边还是进行校验
        ak.start_date = pd.to_datetime(row['turnover_date']).date() + timedelta(hours=8)
        ak.end_date = pd.to_datetime(row['date']) + timedelta(hours=18)
        ak.ktype = k_type
        df = ak.get_k_data()
        return df.shape[0]  #返回K线数量（这里没有按日期进行汇总，是区间内的总K线数）、
    
if __name__=="__main__":
    #1. 初始化
    a = cum_turnover()
    a.code = '603099.sh'
    a.start_date = datetime(2023,12,20,8)
    a.end_date = datetime(2024,1,23,18)
    a.ktype = '1d'
    a.update_price_range_1d_by_code()
    #2. 读取全换手数据
    sql_str = f"SELECT * FROM stock.tspro_cumulative_turnover WHERE CODE='{a.code}' AND date(date) between '{a.start_date.date()}' and '{a.end_date.date()}'"
    df_db = pd.read_sql(sql_str , a.engine)
    print(df_db)

    #3. 循环读取数据库中的日期，进行元素级别操作
    #df_db['K线数量'] = df_db.apply(__lambda_K线校验 , k_type = '1m' , axis = 1)

    #这一表明得到全部的价格分布
    #df_db['价格分布'] = df_db.apply(__lambda_价格区间 , k_type = a.ktype , axis = 1)
    #得到最last的价格分布
    df_db['价格分布'] = __lambda_价格区间(df_db.iloc[-1] ,k_type = a.ktype )
    #----画出df的K线（价格走势）----
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    #mpf.plot(df, type='candle', style='charles', title='K线图', ylabel='价格')
