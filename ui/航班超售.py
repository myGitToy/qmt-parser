from scipy.stats import binom
import numpy as np

def overbooking(Capicity, Spill_cost, DB_cost, NO_show_ratio):
    """
    这是一个Matlab函数，用于计算航班的最优超售数量和相应的超售成本。
    函数的输入参数包括航班的容量（Capicity）、溢出成本（Spill_cost）、
    被拒绝登机的成本（DB_cost）和未出现的比率（NO_show_ratio）。
    函数的输出是最大销售量（Max_sale）和总成本（Total_cost）。
    函数的主要逻辑是通过一个循环来找出使总成本最小的超售数量。循环从航班的容量开始，一直到3000。在每次循环中，它计算出总成本，这个成本是由两部分组成的：如果实际出现的乘客数量小于航班的容量，那么成本就是溢出成本乘以未使用的座位数量；如果实际出现的乘客数量大于航班的容量，那么成本就是被拒绝登机的成本乘以超出的乘客数量。这个成本是按照二项分布的概率加权的。

    如果当前的总成本小于前一次的总成本，那么就更新总成本。否则，就认为找到了最优的超售数量（即当前的超售数量减一），并将总成本设置为前一次的总成本，然后跳出循环。

    最后，函数返回最大销售量和总成本。
    """
    # 计算出航班最优的超售数量与相应的超售成本
    # 输入
    #   Capicity
    #   Spill_cost
    #   DB_cost
    #   NO_show_ratio
    # 输出
    #   Max_sale
    #   Total_cost

    Total_cost_pre = np.inf
    for i in range(Capicity, 3001):
        Total_cost = 0
        for j in range(i+1):
            if j < Capicity:
                Total_cost = Total_cost + binom.pmf(j, i, 1-NO_show_ratio) * Spill_cost * (Capicity-j)
            else:
                Total_cost = Total_cost + binom.pmf(j, i, 1-NO_show_ratio) * DB_cost * (j-Capicity)
        if Total_cost < Total_cost_pre:
            Total_cost_pre = Total_cost
        else:
            Max_sale = i-1
            Total_cost = Total_cost_pre
            break
    return Max_sale, Total_cost