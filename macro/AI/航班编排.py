import pandas as pd
import numpy as np
from scipy.optimize import linprog
from scipy.stats import norm

# 读取数据
flight = pd.read_excel('.\timetable.xlsx').values
aircrafttype = pd.read_excel('.\aircraft_typ.xlsx').values
demand = pd.read_excel('.\flightdemand.xlsx').values

flihgt_amount = flight.shape[0]
type_amount = aircrafttype.shape[0]
X_ij_amount = flihgt_amount * type_amount
G_k_amount = flihgt_amount * 2 * type_amount

# 目标函数的矩阵
target_Matrix = np.zeros(X_ij_amount + G_k_amount)
oper_cost = np.zeros((flihgt_amount, type_amount))
spill_cost = np.zeros((flihgt_amount, type_amount))
total_cost = np.zeros((flihgt_amount, type_amount))

for i in range(type_amount):
    for j in range(flihgt_amount):
        oper_cost[j, i] = aircrafttype[i, 0] * demand[j, 3] * aircrafttype[i, 2]
        spill_cost[j, i] = aircrafttype[i, 1] * demand[j, 3] * (demand[j, 5] / (2 * np.pi ** 0.5) * np.exp(-(aircrafttype[i, 2] - demand[j, 4]) ** 2 / (2 * demand[j, 5] ** 2)) + (demand[j, 4] - aircrafttype[i, 2]) * (1 - norm.pdf((aircrafttype[i, 2] - demand[j, 4]) / demand[j, 5])))
        total_cost[j, i] = oper_cost[j, i] + spill_cost[j, i]

temp_matrix = total_cost.flatten(order='F')
target_Matrix[:type_amount * flihgt_amount] = temp_matrix

# 航班覆盖约束矩阵
A_flightcover = np.zeros((flihgt_amount, X_ij_amount + G_k_amount))
for i in range(flihgt_amount):
    for j in range(type_amount):
        A_flightcover[i, i + j * flihgt_amount] = 1
b_flightcover = np.ones(flihgt_amount)

# 时空节点
# 到达时空节点
depart_spot = flight[:, :3]
depart_spot = np.c_[depart_spot, np.full((depart_spot.shape[0], 1), -1)]

# 出发时空节点
arrival_spot = flight[:, :1]
arrival_spot = np.c_[arrival_spot, flight[:, 3:5], np.full((arrival_spot.shape[0], 1), 1)]

temp_S1 = np.r_[depart_spot, arrival_spot]
time_spot = temp_S1[temp_S1[:, 1].argsort()]

# 变量的边界
lb_xij = np.zeros(flihgt_amount * type_amount)
ub_xij = np.ones(flihgt_amount * type_amount)
lb_Gkj = np.zeros(flihgt_amount * 2 * type_amount)
ub_Gkj = np.zeros(flihgt_amount * 2 * type_amount)
for i in range(type_amount):
    aa = aircrafttype[i, 3]
    ub_Gkj[flihgt_amount * 2 * i: flihgt_amount * 2 * (i + 1)] = aa

lb = np.r_[lb_xij, lb_Gkj]
ub = np.r_[ub_xij, ub_Gkj]

# 线性规划求解
c = target_Matrix
A_eq = A_flightcover
b_eq = b_flightcover
bounds = [(lb[i], ub[i]) for i in range(len(lb))]

# 输出结果
result = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds)
x = result.x