"""
测试pandans对于excel文件的读取功能

1. 默认引擎为xlrd，目前高版本已不支持xlsx文件
2. 切换引擎至openpyxl 
3. 上述两个引擎都需要额外pip install
4. 表的名称和列的名称目前都支持中文
5. 读取时excel表格必须处于关闭状态，否则会报错（通过增加exception可以做到提示错误信息）

"""

import pandas as pd
def read_excel():
    #文件读取
    try:
        df = pd.read_excel('.\\data\\zxg.xlsx' , sheet_name = '33指数' , engine = 'openpyxl' )
        return df
    except Exception as e:
        print(str(e))
        return pd.DataFrame()
a = read_excel()
print (a)
a.to_excel('.\\data\\zxg_write.xlsx', sheet_name='11',  header=True, index=False)