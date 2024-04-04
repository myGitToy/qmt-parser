"""
分析上航2023-2024通宵航班的着陆距离情况
"""
import pandas as pd

#打开excel文件中的RawData数据表
df = pd.read_excel('C:\\Users\\george\\Desktop\\通宵航班分析.xlsx', sheet_name='RawData')
#去除降落时间为-的行
df = df[df['降落时间'] != '-']
#将降落时间列进行时间序列化
df['降落时间'] = pd.to_datetime(df['降落时间'], errors='coerce')
#新增一列，如果降落时间在16:00-23:59之间，标记为1，否则为0
df['是否通宵'] = df['降落时间'].apply(lambda x: 1 if x.hour >= 18 else 0)
df.to_excel('C:\\Users\\george\\Desktop\\通宵航班分析_结果.xlsx', sheet_name='RawData', index=False)
#列出起飞机场为VTSP的航班，以及是否通宵
print(df[df['起飞机场'] == 'VTSP'][['起飞机场','是否通宵']])
#画出降落时间的分布图
df['降落时间'].dt.hour.hist()
#画出通宵航班的降落时间分布图
df[df['是否通宵'] == 1]['降落时间'].dt.hour.hist()
#画出非通宵航班的降落时间分布图
df[df['是否通宵'] == 0]['降落时间'].dt.hour.hist()


