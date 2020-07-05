# -*- coding: utf-8 -*-

"""
量化交易中五大工具：
统计套利: statistics arbitrage
高频交易：high frenquency trading
量化投资：quantitative investment
算法交易：algorithm trading
程序化交易：program trading

本程序取自算法交易和程序化交易的首字母
apt即algorithm & program trading
"""
def print_tree_list():
    print('''
    根目录：
    data #数据目录 程序使用tushare下载的csv文件目录
    apt #算法&程序化交易主目录
        -data #数据处理目录
        -fund #基金相关 每日净值处理等
        -trade #交易操作 买入卖出等
        -os #文件操作 文件读取
        -strategy #策略文件
    
    
    ''')
