from jqdatasdk import *
import sqlalchemy
class base():
    """
    jqdata中的一些基础数据
    """
    def __init__(self):
        auth('13817092632','JQ@tushare123') 
        self.engine = sqlalchemy.create_engine('mysql+pymysql://stock_user:a@1#Yy1c@localhost:3306/stock')

