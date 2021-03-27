import pandas as pd
def read_excel():

    #文件读取
    try:
        df = pd.read_excel('.\\data\\zxg.xlsx' , sheet_name = '33指数',  engine = 'openpyxl')
        return df
    except IOError:
        print("无可用文件，请检查！")
        return pd.DataFrame()

a = read_excel()
print (a)
#,encoding = 'utf-8'