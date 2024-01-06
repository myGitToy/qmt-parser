#使用有监督的机器学习，对Dataframe中的数据进行分析
#使用sklearn中的线性回归模型，对数据进行分析

#使用sklearn中的决策树模型，对数据进行分析
#使用sklearn中的随机森林模型，对数据进行分析
#使用sklearn中的SVM模型，对数据进行分析
#使用sklearn中的KNN模型，对数据进行分析
#使用sklearn中的K-Means模型，对数据进行分析
#使用sklearn中的PCA模型，对数据进行分析
#使用sklearn中的LDA模型，对数据进行分析
#使用sklearn中的AdaBoost模型，对数据进行分析
#使用sklearn中的GBDT模型，对数据进行分析
#使用sklearn中的XGBoost模型，对数据进行分析
#使用sklearn中的LightGBM模型，对数据进行分析
#使用sklearn中的CatBoost模型，对数据进行分析

import pandas as pd
#读取excel文件，sheet1中的A-I列
df = pd.read_excel('.\\data\\关系矩阵.xlsx',sheet_name = 'Sheet1',usecols = 'A:I')
#print(df)

#绘制相关系数矩阵图
import seaborn as sns
import matplotlib.pyplot as plt
#绘制热力图
plt.figure(figsize=(10, 10))
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体为黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
sns.heatmap(df.corr(), annot=True, vmax=1, square=True, cmap="Blues")
plt.show()

#使用z-score方法进行数据标准化
from sklearn.preprocessing import StandardScaler
#标准化，返回值为标准化后的数据
df_standard = StandardScaler().fit_transform(df)
print(df_standard)

#使用SVM模型进行数据分析
from sklearn import svm
#创建SVM回归模型
clf = svm.SVR()
#拟合训练数据集
clf.fit(df_standard,df['着陆距离'])
#预测测试集
predict = clf.predict(df_standard)
print(predict)

#查看预测偏差（未拆分训练集和预测集）
df['着陆距离预测'] = predict
df['预测偏差'] = (df['着陆距离预测'] - df['着陆距离'])/df['着陆距离']
df[['着陆距离','着陆距离预测','预测偏差']].to_csv('.\\data\\SVM距离线性模型.csv',encoding='utf-8-sig')

