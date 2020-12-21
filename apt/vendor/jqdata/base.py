from jqdatasdk import *
import sqlalchemy
from enum import Enum
class base():
    """
    jqdata中的一些基础数据
    """
    class 交易时段校验(Enum):
        """
        检查当天日期是否是交易日和交易时段
        非交易时段 定义为 交易日的非交易时段
        """
        非交易日 = 0
        非交易时段 = 1
        交易时段 = 2
    class 数据源(Enum):
        """
        设置jqdata的数据源
        """
        aliyun = 0
        aws = 1
        localhost = 2
        nas = 3

    def __init__(self , rds_host = 数据源.localhost):

        if rds_host == self.数据源.aliyun:
            print("aliyun 暂不支持")
        elif rds_host == self.数据源.aws:
            print("aws 暂不支持")
        elif rds_host == self.数据源.localhost:
            self.engine = sqlalchemy.create_engine('mysql+pymysql://stock_user:a@1#Yy1c@localhost:3306/stock')
            auth('13817092632','JQ@tushare123')
        elif rds_host == self.数据源.nas:
            print("nas 暂不支持")
        else:
            print("不支持的数据源，授权无效")
        
        

