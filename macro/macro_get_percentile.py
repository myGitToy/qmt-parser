'''
此模块用于获取指定代码的百分数位置
'''
from datetime import datetime
from apt.qsp_universal.prank import prank as prank

rank = prank()
rank.code = '002049.sz'
rank.end_date = datetime(2022,5,20)
print(rank.get_prank(N = 180)[['date','code','close','p75','p85','p90']])