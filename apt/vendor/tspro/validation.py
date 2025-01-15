import pandas as pd
import numpy as np
from datetime import datetime,timedelta
from apt.vendor.tspro.data import data as ts_data
from datetime import datetime

class Validation(ts_data):
    """
    校验类
    如检查日线 分时线数据是否完整等
    """
    def __init__(self):
        #初始化父类
        super().__init__()

    def check_k_data(self) -> tuple[bool, pd.DataFrame]:
        """
        检查K线数据的有效性
        规则：
        1. 日线默认全部收录，不进行校验
        2. 分时线与日线进行交叉校验，返回2个参数
            参数1：是否通过校验 True/False
            参数2：未通过校验的日期 DataFrame
        【输入】
            (继承自ts_data)
            code：证券代码
            ktype：K线类型
            start_date：开始日期
            end_date：结束日期
        """
        #数据校验，如果start_date和end_date只包含日期，自动加上时间
        if isinstance(self.start_date , datetime):
            self.start_date = datetime(self.start_date.year , self.start_date.month , self.start_date.day , 8)
        if isinstance(self.end_date , datetime):
            self.end_date = datetime(self.end_date.year , self.end_date.month , self.end_date.day , 16)
        #校验是否是日线数据
        if self.ktype == '1d':
            return True
        else:
            #取出分时线对应的每天的个数
            sql_min = f"select date(date) as date,count(date) as count from tspro_{self.ktype} where date >= '{self.start_date}' and date <= '{self.end_date}' and code = '{self.code}' group by date(date)"
            df_min = pd.read_sql(sql_min , self.engine) 
            #获取日线
            sql_day = f"select date(date) as date,count(date) as count from tspro_1d where date >= '{self.start_date.date()}' and date <= '{self.end_date.date()}' and code = '{self.code}' group by date(date)"
            df_1d = pd.read_sql(sql_day , self.engine) 
            #用分时线和日线进行比较(日线和分时线在同一天都需要有数据即可)
            df_1d['valid'] = df_1d['date'].apply(lambda x: True if x in df_min['date'].values else False)
            #如果valid全部为True ，返回True；否则返回False 并且再返回一个值 所有False的日期
            if df_1d['valid'].values.all():
                return True
            else:
                return False , df_1d.query('valid == False')[['date','valid']]


if __name__ == '__main__':
    a = Validation()
    a.code = '600519.SH'
    a.start_date = datetime(2024,1,1,8)
    a.end_date = datetime(2024,4,30,16)
    a.ktype = '60m'
    valid = a.check_k_data()
    #打印valid的第一个值

    if isinstance(valid, bool):
        print(valid)
    else:
        print(valid[0])
    if valid[0] == False:
        print(valid[1])
    #print(a.ktype)
