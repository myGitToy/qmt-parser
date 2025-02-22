# -*- coding: utf-8 -*-
from apt.vendor.jqdata.jqdata import data as jqdata
from apt.vendor.jqdata.base import base as jqbase
from apt.vendor.tspro.data import data as tsdata
from apt.vendor.akshare.data import data as akdata
from apt.vendor.tspro.security import security as tssec
from apt.vendor.jqdata.security import security as jqsec
from datetime import datetime , timedelta
from enum import Enum
from dotenv import load_dotenv #用于读取.env文件
import os   #用于读取文件目录
import numpy as np
import pandas as pd
import tushare as ts

class base():
    """
    量化选股系统的基类(通用数据接口)
    """
    class vendor(Enum): 
        """
        选择数据供应商接口
        默认为tusharePro
        """
        tushare = 0 #tushare（未实装）
        tusharePro = 1 #tusharePro
        jqdata = 2 #jqdata
        akshare = 3   #akshare
    class 复权(Enum):
        """
        选择复权类型
        默认为动态复权
        """
        不复权 = 0 #不进行复权处理
        前复权 = 1 #以最新日期基准，向前进行复权
        后复权 = 2 #以开始日期为基准，向后进行复权
        动态复权 = 3   #以结束日期为基准，向前进行复权
    def __init__(self , code = None , start_date = datetime(2021,1,1), end_date = datetime.now() , ktype = "1d" , fq = 复权.动态复权 , fwq = jqdata.数据源.localhost , myauth = False , vendor = vendor.tusharePro):
        """
        初始化
        输入：
            code 证券代码   e.g. 510300.XSHG
            start：开始日期  e.g. datetime
            end：结束日期    e.g. datetime
            ktype：K线类型 e.g. 1d 5m 30m 60m 
            fq：复权类型 默认动态复权
            fwq：服务器 默认为localhost
            myauth：是否向vendor进行登陆授权，默认是False；量化选股的设计初衷就是脱机本地读取数据
        返回：
        """
        self.code = code
        self.start_date = start_date
        self.end_date = end_date
        self.ktype = ktype
        self.fq = fq
        self.myauth = myauth
        self.server = fwq
        self.vendor = vendor
        #读取.env文件
        load_dotenv()
        #初始化ts接口
        self.pro = ts.pro_api(os.getenv('TUSHARE_TOKEN'))
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

    def get_k_data(self , count = None , col = ['code','date','open','close','high','low','volume','money','factor'] , flag_forward = False , flag_resample = False):
        """
        通用数据接口 获取指定日期间的K线数据
        由于tushare目前不含factor数据，因此本模块未完全可用
        输入（jqdata数据类型）：
            无
        输入（tusharePro数据类型）：
        count: 获取K线条目的个数 默认是全部输出  
        flag_forward：用于获取N日之后X条数据，类似于后复权数据 默认为False
            在这种模式下，start_date为基准日期，先后输出count条数据
            其余模式end_date均为基准日期
            详见https://huiqiao.visualstudio.com/MyFunds/_workitems/edit/296
        flag_resample：T/F 用于标识是否进行重采样
            目前仅对60分钟线有效
            True：进行重采样
            False：不进行重采样，舍弃9:30单根数据
        返回：
            dataframe ：包含开盘 收盘 最高 最低 成交量 成交额 代码
        """
        if self.vendor == self.vendor.tusharePro:
            a = tsdata()
            a.myauth = self.myauth
            a.数据源 = self.server
            a.start_date = self.start_date
            a.end_date = self.end_date
            a.fq = self.fq
            a.code = self.code
            a.ktype = self.ktype
            df = a.get_k_data(count = count , col = col , flag_forward = flag_forward , flag_resample = flag_resample)
            return df
        elif self.vendor == self.vendor.jqdata:
            a = jqdata(rds_host = self.server , myauth = self.myauth) 
            #此处的get_k_data从vendor.jqdata.data.get_k_data取数据，非tushare
            df = a.get_k_data(code = self.code , start_date = self.start_date , end_date = self.end_date , ktype = self.ktype , fq = self.fq , count = count , flag_forward = flag_forward)
            return df
        elif self.vendor == self.vendor.akshare:
            a = akdata()
            a.myauth = self.myauth
            a.数据源 = self.server
            a.start_date = self.start_date
            a.end_date = self.end_date
            a.fq = self.fq
            a.code = self.code
            a.ktype = self.ktype
            df = a.get_k_data(count = count , col = col , flag_forward = flag_forward , flag_resample = False)
            return df
        else:
            raise ValueError(f'不支持此数据供应商，请检查输入！')

    def get_all_code(self , type = type):
        """
        通用数据接口 获取指定日期节点依旧上市的证券代码列表
        输入：
            type 证券类别 默认为['stock','etf']
            隐藏层 day = self.end_date
        返回：
            dataframe ：
        """
        if self.vendor == self.vendor.tusharePro:
            a = tssec()
            #获取证券列表            
            return a.get_all_code(day = self.end_date)
        elif self.vendor == self.vendor.jqdata:
            a = jqsec()
            #获取证券列表
            return a.get_all_code(day = self.end_date , type = type)
        elif self.vendor == self.vendor.akshare:
            #目前akshare采用tspro证券列表
            a = tssec()
            #获取证券列表            
            return a.get_all_code(day = self.end_date)
        else:
            raise ValueError(f'不支持此数据供应商，请检查输入！')

    def get_security(self , code = None):
        """
        通用数据接口 获取指定证券代码的相关信息（简单版目前仅提供stock或ETF的分类）
        输入：
            code 证券代码
        返回：
            dataframe , string
                df[0]:dataframe: code|market|name
                df[1]:string: stock|etf|nan
        """
        if code == None:
            code = self.code
        if self.vendor == self.vendor.tusharePro:
            a = tssec()
            #获取证券列表            
            return a.get_security(code = code)
        elif self.vendor == self.vendor.jqdata:
            a = jqsec()
            #获取证券列表
            return a.get_security(code = code)
        elif self.vendor == self.vendor.akshare:
            #目前akshare采用tspro证券列表
            a = tssec()
            #获取证券列表            
            return a.get_security(code = code)
        else:
            raise ValueError(f'不支持此数据供应商，请检查输入！')

    def get_rolling_k_等待删除(self , ktype = "1d"):
        """
        【此处不确定是否需要删除 目前看没有引用】
        抽取出来的总类，用于获取最新的K线数据，含自动更新
        输入：
            ktype：K线类型 e.g. D 60 30
        返回：
            根据K线类型计算出来的当日K线总条数 
        """
        if ktype == "1d":
            #日线数据
            return 1
        elif ktype in ('15m','30m','60m'):
            #K线数据（文本类型）
            return 60 / int(ktype[0:2]) * 4
        elif ktype in ('5m'):
            return 48
        elif ktype in ('1m'):
            #K线数据（数字类型）
            return 240
        else:
            print("K线类型输入无效，按照默认日线数据返回结果")
            return 1

    def read_excel(file_name = None , sheet_name = None):
        """
        读取excel数据
        注意事项：
            1. 默认引擎为xlrd，目前高版本已不支持xlsx文件
            2. 切换引擎至openpyxl 
            3. 上述两个引擎都需要额外pip install
            4. 表的名称和列的名称目前都支持中文
            5. 读取时excel表格必须处于关闭状态，否则会报错（已通过增加exception做到提示错误信息）
        """
        try:
            df = pd.read_excel( file_name, sheet_name = sheet_name , engine = 'openpyxl' )
            return df
        except Exception as e:
            print(str(e))
            return pd.DataFrame()