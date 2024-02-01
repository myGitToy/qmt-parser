"""
更新全部的财务指标入库
"""
from datetime import datetime
from apt.vendor.tspro.security import security
from apt.vendor.tspro.finance_indicator import finance_indicator

#设置参数
ind = finance_indicator()
ind.end_date = datetime(2023,12,31)

#获取所有证券代码
sec = security()
all_codes = sec.get_all_code(day = ind.end_date , type = ['stock'])
for code in all_codes['code']:
    ind.code = code
    ind.update_finance_indicator()


