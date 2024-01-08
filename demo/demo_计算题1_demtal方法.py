import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#新建一个6*6的矩阵
a = np.array([[0.2, 0.05, 0.25, 0, 1.95, 0.35],
       [0.1, 0.1, 0.55, 0, 0, 0.05],
       [0, 0.8, 0.2, 0.5, 0.25, 0.75],
       [0.2, 0, 0, 0, 0.15, 0.45],
       [0.51, 0.25, 0, 0.2, 0, 0.9],
       [0.22, 0.15, 0.12, 0.5, 0, 0]])
#填入df的值
df = pd.DataFrame(a,columns=['C1','C2','C3','C4','C5','C6'],index=['C1','C2','C3','C4','C5','C6'])
#增加行和和列和
df['行和'] = df.apply(lambda x: x.sum(), axis=1)
df.loc['列和'] = df.apply(lambda x: x.sum())
#计算DEMATEL方法中的原因度
#原因度=行和 - 列和的转置矩阵
df['原因度'] = df['行和'] - df.loc['列和'].T
#计算DEMATEL方法中的中心度
#原因度=行和 + 列和的转置矩阵
df['中心度'] = df['行和'] + df.loc['列和'].T
print(df)
#绘制中心度-原因度图（基于笛卡尔直角坐标）
#X轴为中心度，Y轴为原因度，坐标系原点为（0，0）
plt.figure(figsize=(10, 6))  # 设置图形大小
plt.scatter(df['原因度'], df['中心度'])  # 绘制散点图
# 添加每个点的注释
for i in range(len(df)):
    plt.annotate(df.index[i], (df['原因度'][i], df['中心度'][i]))
plt.title('中心度-原因度图')  # 设置图形标题
plt.xlabel('原因度')  # 设置x轴标签
plt.ylabel('中心度')  # 设置y轴标签
plt.grid(True)  # 添加网格线
plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体为黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像时负号'-'显示为方块的问题
plt.show()  # 显示图形


df['影响度'] = df['行和'] / df.loc['列和', '行和']
#计算原因度
df['原因度'] = df['行和'] / df.loc['列和', '行和']
#计算中心度
df['中心度'] = df['原因度'] / df['原因度'].sum()
print(df)


#为综合相关影响矩阵，求出df的关键参量

