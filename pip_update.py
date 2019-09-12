import pip
from subprocess import call
from pip._internal.utils.misc import get_installed_distributions
for dist in get_installed_distributions():
    call("pip install --upgrade " + dist.project_name, shell=True)
#————————————————
#版权声明：本文为CSDN博主「yuzhucu」的原创文章，遵循 CC 4.0 BY-SA 版权协议，转载请附上原文出处链接及本声明。
#原文链接：https://blog.csdn.net/yuzhucu/article/details/80287307
