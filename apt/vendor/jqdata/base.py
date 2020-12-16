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

    def __init__(self):
        auth('13817092632','JQ@tushare123') 
        self.engine = sqlalchemy.create_engine('mysql+pymysql://stock_user:a@1#Yy1c@localhost:3306/stock')

