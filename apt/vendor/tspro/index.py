import numpy as np
import pandas as pd
import tushare as ts
import akshare as ak
import sqlalchemy
import time
#from apt.qsp_universal.base import base as kdata
#from apt.vendor.akshare.base import base as akdata
#import datetime
from scipy import stats
from datetime import datetime,timedelta
from apt.vendor.tspro.data import data as tspro_data
from apt.vendor.tspro.security import security as sec

class idx(tspro_data):
    """
    专门处理板块的类
    """
    def __init__(self):
        super().__init__()
        self._name = 'idx'
    def get_index(self):
        """
        获取指数
        """
        print('获取指数')



class idx_SW(idx):
    """
    申万板块
    接口：index_classify
    描述：获取申万行业分类，可以获取申万2014年版本（28个一级分类，104个二级分类，227个三级分类）和2021年本版（31个一级分类，134个二级分类，346个三级分类）列表信息
    说明：目前申万只能获取分类表，指数每日行情暂时无渠道获取
    """
    def __init__(self):
        super().__init__()   

    def get_SW_classify(self , local_db = False , level = 'L1', src = 'SW2021' , is_pub = None):
        """
        获取申万板块
        【输入】
            local_db：是否从本地数据库获取，默认为False
            level：L1/L2/L3
            src：行业分类 SW2014/SW2021
            is_pub：指数是否编制（少于5个代码的指数将不进行编制） 1/0         
        """
        #输入参数的校验
        if level not in ['L1','L2','L3']:
            raise ValueError('level参数只能是L1/L2/L3')
        if src not in ['SW2014','SW2021']:
            raise ValueError('src参数只能是SW2014/SW2021')
        if is_pub not in [None,1,0,'1','0']:
            raise ValueError('is_pub参数只能是None,1,0')
        #对is_pub进行转换，默认接受数字，如果是字符串，则转换成数字
        if isinstance(is_pub,str) and is_pub != None:
            is_pub = int(is_pub)
        df_api = self.pro.index_classify(**{
                    "index_code": "",
                    "level": level,
                    "src": src,
                    "parent_code": "",
                    "limit": "",
                    "offset": ""
                }, fields=[
                    "index_code",
                    "industry_name",
                    "level",
                    "industry_code",
                    "is_pub",
                    "parent_code",
                    "src"
                ])
        #对is_pub进行判断，None代表返回全部，1代表返回公开，0代表返回未公开
        #注意：is_pub字段的属性在这里是text，不是int
        if is_pub == 1:
            #返回is_pub = 1的行业
            df_api = df_api[df_api['is_pub'] == '1']
        elif is_pub == 0:
            df_api = df_api[df_api['is_pub'] == '0']
        else:
            pass
        return df_api

    def get_SW_member(self , local_db = False , index_code = '' , is_new = '' , ts_code = ''):
        """
        获取申万板块
        【输入】
            local_db：是否从本地数据库获取，默认为False
            index_code：指数代码
            is_new：是否最新成分 Y/N
            ts_code: 成分股代码
        方法1：index_code 获取申万L1/L2/L3成分股
        方法2：ts_code 获取成分股所属申万板块（包含全部的板块，不仅仅局限于L1-L3）
        """
        #输入参数的校验
        if is_new not in ['Y','N','']:
            raise ValueError('is_new参数只能是Y/N/null')
        df_api = self.pro.index_member(**{
                    "index_code": index_code,
                    "is_new": is_new,
                    "ts_code": ts_code,
                    "limit": "",
                    "offset": ""
                }, fields=[
                    "index_code",
                    "con_code",
                    "in_date",
                    "out_date",
                    "is_new",
                    "index_name",
                    "con_name"
                ])
        return df_api

    def update_SW_classify(self, level = 'L1', src = 'SW2021'):
        """
        更新申万板块\n
        【输入】
            level：L1/L2/L3
            src：行业分类 SW2014/SW2021
        """
        df_api = self.pro.index_classify(**{
                    "index_code": "",
                    "level": level,
                    "src": src,
                    "parent_code": "",
                    "limit": "",
                    "offset": ""
                }, fields=[
                    "index_code",
                    "industry_name",
                    "level",
                    "industry_code",
                    "is_pub",
                    "parent_code",
                    "src"
                ])
        return df_api
        print('更新申万板块')


class BI:
    """
    申万行业/同花顺报表

    """
    def __init__(self):
        self.idx_sw = idx_SW()  # 创建 idx_SW 的实例
        self.idx_ths = idx_THS()  # 创建 idx_THS 的实例 
    def dashboard_SW_10周动量(self, level = 'L2' , is_pub = 1 , minimum_show = 5):
        """
        申万行业10周动量看板
        默认使用L2级别的行业分类；默认只显示有指数编制的行业分类
        minimum_show 只显示成分股数大于等于X的行业分类 默认为5（未实装）
        输出：
        行业分级	行业名称	M0	P0	M1	P1	M2	P2
        其中M0代表T周的涨跌幅，P0代表最近T周的分位数排名（0-1之间，0.99代表排名靠前，是涨幅最大的1%）
        """
        #输入参数的校验
        if level not in ['L1','L2','L3']:
            raise ValueError('level参数只能是L1/L2/L3')
        if is_pub not in [None,1,0,'1','0']:
            raise ValueError('is_pub参数只能是None,1,0')
        #获取申万行业的第一层目录
        df_L1 = self.idx_sw.get_SW_classify(level = level , is_pub = is_pub)
        #输出的报表格式如下：行业分级	行业名称	M0	P0	M1	P1	M2	P2
        #其中M0代表T周的涨跌幅，P0代表最近T周的排名
        #M1代表T-1周的涨跌幅，P1代表最近T-1周的排名
        #输出的报表中，行业分级和行业名称只输出一次
        #定义报表格式
        df_report = pd.DataFrame(columns=['行业分级','行业名称','成分股数','权重得分','M0','P0','M1','P1','M2','P2','M3','P3','M4','P4','M5','P5','M6','P6','M7','P7','M8','P8','M9','P9','M10','P10'])
        #定义M0-M10列和P0-P10列，series类型，用于后续计算
        cols_P = [col for col in df_report.columns if col.startswith('P')]
        cols_M = [col for col in df_report.columns if col.startswith('M')]
        #获取该层目录的10周K线数据
        for code in df_L1.tail(2000)['index_code']:
            #行业分级 = level
            df_report.loc[df_L1[df_L1['index_code'] == code].index[0],'行业分级'] = f"申万{level}"
            #行业名称 = industry_name
            df_report.loc[df_L1[df_L1['index_code'] == code].index[0],'行业名称'] = df_L1[df_L1['index_code'] == code]['industry_name'].values[0]
            #成分股数
            df_report.loc[df_L1[df_L1['index_code'] == code].index[0],'成分股数'] = len(self.idx_sw.get_SW_member(index_code = code))
            df_L1_week = ak.index_hist_sw(symbol=code[0:6], period="week")
            #取最后15行数据
            df_L1_week = df_L1_week.tail(15)
            #计算涨跌幅
            df_L1_week['pct_chg'] = df_L1_week['收盘'].pct_change()
            #倒数第N行数据填充入Mn
            for n in range(11):
                df_report.loc[df_L1[df_L1['index_code'] == code].index[0], f'M{n}'] = df_L1_week['pct_chg'].iloc[-n-1]
        #用M列的Y轴数据计算分位数，写入P列
        df_report[cols_P] = df_report[cols_M].apply(lambda x: x.rank(pct = True))  
        """
        方法2：使用for循环实现          
        for n in range(11):
            #ascending=True，那么元素将按照升序进行排名，即较小的值将有较低的排名。
            df_report[f'P{n}'] = df_report[f'M{n}'].rank(pct = True , ascending = True)
        """
        #计算EMA权重
        weights = [0.1818, 0.1487, 0.1216, 0.0995, 0.0815, 0.0667, 0.0546, 0.0447, 0.0366, 0.0300, 0.0245]            
        #对选择的列与权重进行元素级别的乘法运算
        #权重计算公式： 0.1818*P0 + 0.1487*P1 + 0.1216*P2 + 0.0995*P3 + 0.0815*P4 + 0.0667*P5 + 0.0546*P6 + 0.0447*P7 + 0.0366*P8 + 0.0300*P9 + 0.0245*P10
        if len(weights) != len(cols_P):
            raise ValueError('权重和列数不匹配')
        df_report['权重得分'] = df_report[cols_P].mul(weights, axis=1).sum(axis=1)
        #print(df_report)
        #存盘
        df_report.to_csv('.\\data\\dashboard_SW_10周动量.csv', encoding = 'utf_8_sig')

class idx_THS(idx):
    """
    同花顺板块
    """
    def __init__(self):
        super().__init__()
    def index_analysis_daily_sw(self):
        """
        akshare指数日线行情
        """
        return ak.index_analysis_daily_sw(symbol='申万Ａ指', start_date="20231003", end_date="20221103")

if __name__ == '__main__':
    a = idx_SW()
    bi = BI()
    bi.dashboard_SW_10周动量()
    #df = a.get_SW_classify(level = 'L2' , is_pub = 1)
    df = a.get_SW_member(index_code = '801971.SI' , is_new='Y')
    aka = idx_THS()
    print(df)
    index_component_sw_df = ak.index_component_sw(symbol="801010")
    print(index_component_sw_df)
    #获取当天的收盘数据
    df_close = a.pro.daily(**{
                "ts_code": "",
                "trade_date": 20240115,
                "start_date": "",
                "end_date": "",
                "offset": "",
                "limit": ""
            }, fields=[
                "ts_code",
                "trade_date",
                "open",
                "high",
                "low",
                "close",
                "pre_close",
                "change",
                "pct_chg",
                "vol",
                "amount"
            ])
    #df_close中的ts_code做变换，由600151.SH的格式变成600151
    df_close['ts_code'] = df_close['ts_code'].str.split('.').str[0]
    #用update命令，将index_component_sw_df中的close列的值更新为df_close中的close列的值
    #index_component_sw_df中的证券代码列改名为ts_close
    index_component_sw_df.rename(columns={'证券代码':'ts_code'},inplace=True)
    index_component_sw_df = index_component_sw_df.set_index('ts_code')
    index_component_sw_df['close'] = df_close.set_index('ts_code')['close']
    
    #通过权重表，计算收盘价求和
    index_component_sw_df['close_sum'] = index_component_sw_df['close'] * index_component_sw_df['最新权重']
    print(index_component_sw_df)
    #输出权重求和的值
    print(index_component_sw_df['close_sum'].sum())
    #print(aka.index_analysis_daily_sw())

    #申万历史行情
    index_hist_sw_df = ak.index_hist_sw(symbol="801010", period="week")
    print(index_hist_sw_df) 
