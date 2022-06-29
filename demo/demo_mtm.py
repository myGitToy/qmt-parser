from datetime import datetime
from apt.qsp_jqdata.momentum import momentum as mtm
from apt.qsp_jqdata.base import base as base
from jqdatasdk import get_ticks
a = mtm()
a.get_mtm(time = datetime(2022,1,1) , ktype = '60m' , code_list = ['601318.XSHG','002059.XSHE'])
#获取tick数据
c = base(myauth = True)
#d = get_ticks("000001.XSHE",start_dt=None, end_dt="2018-07-02", count=10)
#get_ticks(沪深A股行情tick数据) 属于付费模块（仅限机构使用），如果您有购买需求，可添加微信号JQData02申请试用或咨询开通
#print(d)
#get_ticks(security, end_dt, start_dt=None, count=None, fields=['time', 'current', 'high', 'low', 'volume', 'money'], skip=True, df=False)