from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR,SVR
from sklearn.metrics import mean_squared_error, mean_absolute_error
import pandas as pd
import matplotlib.pyplot as plt

# 导入数据
data = pd.read_csv('.\passenger_data.csv')

# 将日期转换为时间戳（数值），以便我们可以在模型中使用它
data['date'] = pd.to_datetime(data['date']).values.astype(float)

# 定义特征和目标变量
X = data['date'].values.reshape(-1, 1)
y = data['passenger_count']

# 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 数据标准化
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# 创建模型，这里有多种模型可以选择
model = SVR()
#model = SVC()
model.fit(X_train, y_train)

# 进行预测
predictions = model.predict(X_test)

# 计算均方误差和平均绝对误差
mse = mean_squared_error(y_test, predictions)
mae = mean_absolute_error(y_test, predictions)

print('计算均方误差:', mse)
print('计算平均绝对误差:', mae)

# 绘制原始旅客量曲线和预测旅客量曲线
plt.figure(figsize=(10, 6))
plt.plot(scaler.inverse_transform(X_test), y_test, label='实际旅客量')
plt.plot(scaler.inverse_transform(X_test), predictions, label='预测旅客量', color='r')
plt.legend()
plt.show()



