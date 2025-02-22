import tushare as ts
import sqlalchemy
import os   #用于读取文件目录
from dotenv import load_dotenv #用于读取.env文件
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
#from apt.vendor.tspro.base import base
@dataclass(order = True)
class base():
    """
    tusharePro基类
    如果需要脱机使用，需初始化如下参数：
    dt = base(myauth = False)
    """
    #myauth : bool = True
    #rds_host : Enum = self.数据源.localhost
    #fq : Enum = 复权.动态复权



    class 交易时段校验(Enum): #计划需要移除
        """
        检查当天日期是否是交易日和交易时段
        非交易时段 定义为 交易日的非交易时段
        """
        非交易日 = 0
        非交易时段 = 1
        交易时段 = 2

    class 数据源(Enum):
        """
        设置tusharePro的数据源
        """
        aliyun = 0
        aws = 1
        localhost = 2
        centos9 = 3
        ubuntu186 = 4
        ubuntu191 = 5

    def __init__(self , rds_host = None , myauth = True):
        """
        tspro 初始化
        rds_host: 数据源的选择 默认为本地数据
        auth: jqdata授权 默认是授权的，False应对某些特殊情况 比如脱机对数据库进行读取操作
        """
        #读取.env文件
        load_dotenv()
        # 进行数据源的选择和映射
        if rds_host is None:    #数据源为空时进行映射
            # 从.env中读取DB_NAME，默认值可以设为"localhost"
            db_name = os.getenv("DB_NAME", "localhost").strip().lower()
            mapping = {
                "aliyun": self.数据源.aliyun,
                "aws": self.数据源.aws,
                "localhost": self.数据源.localhost,
                "centos9": self.数据源.centos9,
                "ubuntu186": self.数据源.ubuntu186,
                "ubuntu191": self.数据源.ubuntu191,
            }      
            rds_host = mapping.get(db_name, self.数据源.localhost)        
        self.myauth = myauth
        if (rds_host == self.数据源.aliyun) and (myauth == True):
            print("aliyun 暂不支持")
        elif rds_host == self.数据源.aws:
            #database-1.cluster-czherlzuxybq.us-west-2.rds.amazonaws.com
            self.engine = sqlalchemy.create_engine(os.getenv('AWS_DB_CONN'))
            #RDS数据库采用Amazon Aurora MySQL Serverless
            if myauth == True:
                #初始化ts接口
                self.pro = ts.pro_api(os.getenv('TUSHARE_TOKEN'))
                self.token = os.getenv('TUSHARE_TOKEN')
        elif rds_host == self.数据源.localhost:
            #self.engine = sqlalchemy.create_engine('mysql+pymysql://root:q19840207@192.168.1.186:3306/stock') #186 ubuntu22LTS
            self.engine = sqlalchemy.create_engine(os.getenv('LOCAL_DB_CONN'))   #dell xps15本地数据库
            #本地数据源支持脱机访问，其他数据源则不支持脱机
            if self.myauth == True:
                #初始化ts接口
                self.pro = ts.pro_api(os.getenv('TUSHARE_TOKEN'))
                self.token = os.getenv('TUSHARE_TOKEN')
        elif rds_host == self.数据源.centos9:
            #self.engine = sqlalchemy.create_engine('mysql+pymysql://stock:sal62688558@192.168.1.188:3306/stock')
            self.engine = sqlalchemy.create_engine(os.getenv('CENTOS9_DB_CONN'))
            #本地数据源支持脱机访问，其他数据源则不支持脱机
            if self.myauth == True:
                #初始化ts接口
                self.pro = ts.pro_api(os.getenv('TUSHARE_TOKEN'))
                self.token = os.getenv('TUSHARE_TOKEN')
        else:
            print("不支持的数据源，授权无效")
        super(base , self).__init__()  #支持多态继承

@dataclass(order = True)
class stock():
#    __tstype = 'D'
    class 复权(Enum): #计划需要移除
        """
        选择复权类型
        默认为动态复权
        """
        不复权 = 0 #不进行复权处理
        前复权 = 1 #以最新日期基准，向前进行复权
        后复权 = 2 #以开始日期为基准，向后进行复权
        动态复权 = 3   #以结束日期为基准，向前进行复权

    def __init__(self , code = None , start_date = datetime(2021,1,1), end_date = datetime.now() , ktype = "1d" , fq = 复权.动态复权  ):
        """
        初始化
        输入：
            code 证券代码   e.g. 510300.XSHG
            start_date：开始日期  e.g. datetime
            end_date：结束日期    e.g. datetime
            ktype：K线类型 e.g. 1d 5m 30m 60m 
            fq：复权类型 默认动态复权
            api:tspro的token信息
            fwq：服务器 默认为localhost
            myauth：是否初始化jqdata授权（需要脱机读取时要设置为False）
            auto_update：数据自动更新 e.g. True False（暂未实装）
        返回：
        """
        self.code = code
        self.start_date = start_date
        self.end_date = end_date
        self.ktype = ktype
        #self.auto_update = auto_update
        self.fq = fq
        self.api = None
        self.dict = {'1d':'D','1m':'1min','5m':'5min','30m':'30min','60m':'60min'}
        #self.myauth = myauth
        #self.server = fwq
        #数据校验环节：
        #1. 证券代码不能为空
        #if code == None:
            #raise ValueError(f'证券代码不能为空')
        #2. 开始日期必须早于结束日期（两个日期start end 必须是同一类型）
        #start和end数据类型统一成datetime(对应bug id：244 未实装)
        #if (isinstance(start , str) == True and :
            #start = datetime.datetime(start)
        if start_date  > end_date:
            raise ValueError(f'开始日期必须早于结束日期')
        #3. K线类型校验
        if ktype not in ('1d','60m','30m','15m','5m','1m'):
            raise ValueError(f'不支持的K线类型：{ktype}')
        super(stock , self).__init__()  #支持多态继承

"""
    @property
    def ktype(self):
        return self.__ktype

    @ktype.setter
    def ktype(self, ktype):
        dict = {'1d':'D','1m':'1min',}
        tstype = dict[self.ktype]
        print(tstype)
        Circle.__ktype = ktype 
"""

if __name__=="__main__":
    a = base(myauth = True)
    df = a.pro.daily(trade_date= '20220602')
    print(df)
