"""
更新全部的财务指标入库
"""
from datetime import datetime
from apt.vendor.tspro.security import security
from apt.vendor.tspro.finance_indicator import finance_indicator

#设置参数，已更新1990-2023/09/30
ind = finance_indicator()
ind.end_date = datetime(2024,3,31)

#获取所有证券代码
sec = security()
all_codes = sec.get_all_code(day = ind.end_date , type = ['stock'] ,)
for code in all_codes['code']:
    ind.code = code
    ind.update_finance_indicator(flag_delete_duplicate=True)

"""
由于更新问题，以下4个代码数据有些紊乱
select code,ann_date,end_date,eps,dt_eps,update_flag from tspro_finance_indicator where code  = '000001.sz' and end_date >= '2020/1/1' order by ann_date
解决方案1可以考虑做数据恢复
000001.SZ财务指标数据已更新，数量：28条
000002.SZ财务指标数据已更新，数量：33条
000004.SZ财务指标数据已更新，数量：27条
000006.SZ财务指标数据已更新，数量：27条
"""
