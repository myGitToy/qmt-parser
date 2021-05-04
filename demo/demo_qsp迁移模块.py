from apt.qsp_jqdata.base import base 

a = base(code = '159949.XSHE' )
df = a.get_k_data() #测试base模块，测试通过
print(df)
