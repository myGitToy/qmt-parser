# -*- coding: utf-8 -*-
import os
import pandas as pd
#定义文件目录，留空则为为当前目录
os.listdir()
list=[]
def list_son_dir(dir_path):
    #获取某个目录下是所有文件名
    file_names = os.listdir(dir_path)
    print(file_names)
    # 遍历每个文件名
    for file_name in file_names:
        # 拼接出这个文件的完整路径
        file_path  = os.path.join(dir_path,file_name)
        # 把路径打印出来
        #print(file_name)
        list.append(file_name)
        # 判断这个路径是不是一个文件夹
        if os.path.isdir(file_path):
            # 如果是文件夹
            list_son_dir(file_path)
        else:
            #如果不是文件夹（是一个文件）,什么都不做
            pass

# 调用这个函数
list_son_dir('D:\\pack\\3000')
#输出结果到df
df = pd.DataFrame(data=list) 
#print(df)
df.to_csv('d:\\song.csv', encoding='utf_8_sig')