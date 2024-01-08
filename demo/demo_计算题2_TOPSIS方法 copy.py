import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#构建假设指标
A = np.array([[1.2, 0.9, 1.1, 8.2, 0.8],
    [1.3, 1, 1.5, 9.7, 1.3],
    [0.8, 1.2,0.7, 5.3, 0.2]])
df_A = pd.DataFrame(A,columns=['C1','C2','C3','C4','C5'],index=['A1','A2','A3'])

#新建一个6*6的矩阵
E = np.array([[1, 3, 2, 7, 5],
    [1/3, 1, 3, 6, 5],
    [1/2, 1/3,1, 5, 4],
    [1/7, 1/6, 1/5, 1, 1/2],
    [1/5, 1/5, 1/4, 2, 1]])
#填入df的值
df_E = pd.DataFrame(E,columns=['C1','C2','C3','C4','C5'],index=['C1','C2','C3','C4','C5'])
#使用向量归一化方法，转换矩阵（这里暂时不需要，否则无法通过一致性检验）
#df_E = df_E.apply(lambda x: x / np.linalg.norm(x), axis=0)
print(df_E)
#一致性检验
n = len(df_E)
# 计算最大特征值
eigenvalues, _ = np.linalg.eig(df_E)
lambda_max = max(eigenvalues.real)
# 计算一致性指标
CI = (lambda_max - n) / (n - 1)
# 随机一致性指标
ri = [0, 0, 0.58, 0.9, 1.12, 1.24, 1.32, 1.41, 1.45, 1.49]
CR = CI / ri[n]
print('lambda最大值：', lambda_max)
print('一致性比率：', CR)

#方案1 TOPSIS法
df_w1 = np.array([[1.5,0.8,0.9,0.6,0.7],
                [0.7,1.5,1.3,0.6,0.6],
                 [1,1,1,1,1]] )
# 确定正理想解和负理想解
positive_ideal_solution = df_w1.max()
negative_ideal_solution = df_w1.min()
# 计算各方案到正理想解和负理想解的距离
distance_positive = np.sqrt(((df_w1 - positive_ideal_solution) ** 2).sum(axis=1))
distance_negative = np.sqrt(((df_w1 - negative_ideal_solution) ** 2).sum(axis=1))
# 计算各方案的相对接近度
closeness = distance_negative / (distance_positive + distance_negative)

# 输出各方案的得分
print('各方案的得分：', closeness)




df = df_A.apply(lambda x: x / np.linalg.norm(x), axis=0)
print(df)
df_w1 = df.mul(w1,axis = 0)
print(df_w1)
#计算最大特征值
df_E['最大特征值'] = df_E['归一化权重'] / df_E.loc['列和', '归一化权重']
#计算行和
df_E['行和'] = df_E.apply(lambda x: x.sum(), axis=1)
#对行和列进行归一化计算
df_normalized_rows = df_E.apply(lambda x: x / x.sum(), axis=1)
df_E.loc['行归一化权重'] = df_normalized_rows.sum().T
print(df_E)
#归一化权重
df_normalized = df_E.apply(lambda x: x / x.sum(), axis=0)
df_E['归一化权重'] = df_normalized.sum(axis=1)

"""
#一致性检验
#计算最大特征值
df_E['最大特征值'] = df_E['归一化权重'] / df_E.loc['列和', '归一化权重']
#计算一致性指标
df_E['一致性指标'] = (df_E['最大特征值'] - 5) / 4
#计算一致性比率
df_E['一致性比率'] = df_E['一致性指标'] / 1.12
#计算平均随机一致性指标
df_E['平均随机一致性指标'] = 0.9
#计算一致性比例
print(df_E)

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

"""