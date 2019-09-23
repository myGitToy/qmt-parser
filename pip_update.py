# -*- coding: utf-8 -*-
"""
文档说明：
    本模块专门进行PYTHON运行环境的更新
    引用规范：不推荐被引用，建议直接运行此文档
    
版本信息：
    version 0.1
    乔晖 2019/9/23

修改日志：
    
[TODO]
1. 无法判断哪些需要更新从而进行有针对性的更新，程序直接进行全部更新，效率比较低     
2. 程序的网络连接速率很低，约10kb/s

"""
import pip
from subprocess import call
from pip._internal.utils.misc import get_installed_distributions
for dist in get_installed_distributions():
    call("pip install --upgrade " + dist.project_name, shell=True)
#————————————————
#版权声明：本文为CSDN博主「yuzhucu」的原创文章，遵循 CC 4.0 BY-SA 版权协议，转载请附上原文出处链接及本声明。
#原文链接：https://blog.csdn.net/yuzhucu/article/details/80287307