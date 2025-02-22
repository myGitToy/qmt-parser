from jqdatasdk import *
from enum import Enum
import sqlalchemy
import os   #用于读取文件目录
from dotenv import load_dotenv #用于读取.env文件
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
        #读取.env文件
        load_dotenv()
        self.myauth = myauth
        if rds_host == self.数据源.aliyun:
            print("aliyun 暂不支持")
            auth(os.getenv('JQDATA_USER'),os.getenv('JQDATA_PASSWORD'))
        elif rds_host == self.数据源.aws:
            #database-1.cluster-czherlzuxybq.us-west-2.rds.amazonaws.com
            self.engine = sqlalchemy.create_engine(os.getenv('AWS_DB_CONN'))
            #RDS数据库采用Amazon Aurora MySQL Serverless
            if myauth == True:
                auth(os.getenv('JQDATA_USER'),os.getenv('JQDATA_PASSWORD'))
        elif rds_host == self.数据源.localhost:
            self.engine = sqlalchemy.create_engine(os.getenv('LOCAL_DB_CONN'))
            #本地数据源支持脱机访问，其他数据源则不支持脱机
            if myauth == True:
                auth(os.getenv('JQDATA_USER'),os.getenv('JQDATA_PASSWORD'))
        elif rds_host == self.数据源.nas:
            print("nas 暂不支持")
            auth(os.getenv('JQDATA_USER'),os.getenv('JQDATA_PASSWORD'))
        else:
            print("不支持的数据源，授权无效")
        
        

