import pandas as pd
df = pd.DataFrame(index=range(1, 16), columns=range(0:15))
print(df)
df.to_csv('output.csv', index=False)
df = pd.read_excel('C:\\test_turtle.xlsx', sheet_name='Sheet1', usecols='M:W', nrows=15)
print(df)
# 将数据转换为所需的格式
data = []
for i in range(12):
    for j in range(12):
        data.append({'X': chr(ord('M') + j), 'Y': i + 1, 'color': df.iloc[i, j]})

# 将数据转换为DataFrame并保存为csv文件
output_df = pd.DataFrame(data)
output_df.to_csv('output.csv', index=False)
