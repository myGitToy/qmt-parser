import pandas as pd
import numpy as np
from datetime import datetime,timedelta
from apt.vendor.akshare.data import data as ak_data
from apt.vendor.akshare.security import security as ak_security
from datetime import datetime

class Validation(ak_data):
    """
    校验类
    如检查日线 分时线数据是否完整等
    """
    def __init__(self):
        #初始化父类
        super().__init__()

    def check_k_data(self) -> tuple[bool, pd.DataFrame]:
        """
        检查K线数据的有效性（按证券代码进行校验）
        规则：
        1. 日线默认全部收录，不进行校验
        2. 分时线与日线进行交叉校验，返回2个参数
            参数1：是否通过校验 True/False
            参数2：未通过校验的日期 DataFrame
        3. 开始日期必须在2023/12/6之后
        4. 由于1分钟线可能会进行存盘，定期将mysql转移至本地hdf5文件，因此mysql中无法保证数据完整性
        
        【输入】
            (继承自ts_data)
            code：证券代码
            ktype：K线类型
            start_date：开始日期
            end_date：结束日期
        """
        #增加aksahre的分时线时间校验
        if self.ktype != '1d' and self.start_date < datetime(2023,12,6):
            #是分时线数据且时间小于2023/12/6，则无法完成校验
            raise Exception('akshare的分时线数据默认包含自2023/12/6起的数据，故开始日期小于此日期则无法完成校验')
            return False
        #数据校验，如果start_date和end_date只包含日期，自动加上时间
        if isinstance(self.start_date , datetime):
            self.start_date = datetime(self.start_date.year , self.start_date.month , self.start_date.day , 8)
        if isinstance(self.end_date , datetime):
            self.end_date = datetime(self.end_date.year , self.end_date.month , self.end_date.day , 16)
        #校验是否是日线数据
        if self.ktype == '1d':
            return True , pd.DataFrame()
        else:
            #取出分时线对应的每天的个数（akshre的数据从2023/12/6起）
            sql_min = f"select date(date) as date,count(date) as count from akshare_{self.ktype} where date >= '{self.start_date}' and date <= '{self.end_date}' and code = '{self.code}' group by date(date)"
            df_min = pd.read_sql(sql_min , self.engine) 
            #获取日线(akshare的日线数据依旧是从tupro中获取的)
            sql_day = f"select date(date) as date,count(date) as count from tspro_1d where date >= '{self.start_date.date()}' and date <= '{self.end_date.date()}' and code = '{self.code}' group by date(date)"
            df_1d = pd.read_sql(sql_day , self.engine) 
            #用分时线和日线进行比较(日线和分时线在同一天都需要有数据即可)
            df_1d['valid'] = df_1d['date'].apply(lambda x: True if x in df_min['date'].values else False)
            #如果valid全部为True ，返回True；否则返回False 并且再返回一个值 所有False的日期
            if df_1d['valid'].values.all():
                return True , pd.DataFrame()
            else:
                return False , df_1d.query('valid == False')[['date','valid']]
            
    def check_k_data_all_code(self , market = ['主板','创业板','中小板','科创板','CDR','北交所'] ):
        """
        在指定日期间，校验全部的1m 5m 60m的数据有效性
        结果存储到文件中
        """
        ak_sec = ak_security()
        ak_sec.start_date = self.start_date
        ak_sec.end_date = self.end_date
        df_code = ak_sec.get_all_code(market = market)
        print('开始校验全部证券的分时线数据')
        
        # 创建结果列表
        results = []
        
        #校验全部1分钟线数据
        for code in df_code['code']:
            self.code = code
            for ktype in ['1m','5m','60m']:
                self.ktype = ktype
                valid = self.check_k_data()
                if valid[0] == True:
                    print(f'{code} |{self.ktype}校验通过')
                    results.append({'code': code, 'ktype': ktype, 'valid': True, 'invalid_dates': None})
                else:
                    print(f'{code}校验未通过，下列日期无数据')
                    print(valid[1])
                    print('------------')
                    results.append({'code': code, 'ktype': ktype, 'valid': False, 'invalid_dates': valid[1].to_dict('records')})
        
        # 转换为DataFrame并保存
        df_results = pd.DataFrame(results)
        df_results.to_csv(f'data_validation_{datetime.now().strftime("%Y%m%d")}.csv', index=False)
        return df_results
        


if __name__ == '__main__':
    a = Validation()
    a.code = '600519.SH'
    a.start_date = datetime(2024,1,1,8)
    a.end_date = datetime(2024,11,25,16)
    a.ktype = '60m'
    a.check_k_data_all_code()


    a.check_k_data()
    valid = a.check_k_data()
    #打印valid的第一个值
    if valid[0] == True:
        print('校验通过')
    else:
        print('校验未通过，下列日期无数据')
        print(valid[1])
        print('------------')

