from jqdatasdk import *
import sqlalchemy
from enum import Enum
class base():
    """
    jqdata基类
    如果需要脱机使用，需初始化如下参数：
    dt = base(myauth = False)
    """
    class 复权(Enum):
        """
        选择复权类型
        默认为动态复权
        """
        不复权 = 0 #不进行复权处理
        前复权 = 1 #以最新日期基准，向前进行复权
        后复权 = 2 #以开始日期为基准，向后进行复权
        动态复权 = 3   #以结束日期为基准，向前进行复权

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

    def __init__(self , rds_host = 数据源.localhost , myauth = True):
        """
        jqdata 初始化
        rds_host: 数据源的选择 默认为本地数据
        auth: jqdata授权 默认是授权的，False应对某些特殊情况 比如脱机对数据库进行读取操作
        """
        self.myauth = myauth
        if rds_host == self.数据源.aliyun:
            print("aliyun 暂不支持")
            auth('18621899367','Qq19840207')
        elif rds_host == self.数据源.aws:
            #database-1.cluster-czherlzuxybq.us-west-2.rds.amazonaws.com
            self.engine = sqlalchemy.create_engine('mysql+pymysql://stock_user:a1#Yy1cTc@database-1.cluster-czherlzuxybq.us-west-2.rds.amazonaws.com:3306/stock')
            #RDS数据库采用Amazon Aurora MySQL Serverless
            if myauth == True:
                auth('18621899367','Qq19840207')
        elif rds_host == self.数据源.localhost:
            self.engine = sqlalchemy.create_engine('mysql+pymysql://stock_user:a@1#Yy1c@localhost:3306/stock')
            #本地数据源支持脱机访问，其他数据源则不支持脱机
            if myauth == True:
                auth('18621899367','Qq19840207')
        elif rds_host == self.数据源.nas:
            print("nas 暂不支持")
            auth('18621899367','Qq19840207')
        else:
            print("不支持的数据源，授权无效")
        
        

