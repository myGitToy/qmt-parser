"""
本模块目的：比较文件夹内mysql dump文件的差异
"""
import os
import re
import sys
import time
import subprocess
from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict
from pprint import pprint


# 设置mysql dump文件夹目录
mysql_dump_folder = 'C:\\Users\\george\\Documents\\dumps'
# 获取mysql dump文件夹列表
mysql_dump_files = os.listdir(mysql_dump_folder)
# 获取mysql dump文件夹列表的绝对路径
for i, file in enumerate(mysql_dump_files):
    mysql_dump_files[i] = os.path.join(mysql_dump_folder, file)
    # 获取每一个文件夹内的文件列表
    mysql_dump_files[i] = os.listdir(mysql_dump_files[i])
    # 获取每一个文件的文件大小
    for j, file in enumerate(mysql_dump_files[i]):
        mysql_dump_files[i][j] = (file, os.path.getsize(os.path.join(mysql_dump_folder, mysql_dump_files[i][j])))

