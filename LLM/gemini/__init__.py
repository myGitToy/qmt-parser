# -*- coding: utf-8 -*-
"""
【google gemini大语言模型】

导入了 logging 模块，这个模块用于在 Python 中进行日志记录。

从当前目录下的 version 模块导入了 __version__ 变量，这个变量通常用于表示当前模块或包的版本号。

从当前目录下的 oai、agentchat、exception_utils 和 code_utils 模块导入了所有的公开接口。这样，其他模块就可以直接通过 import vertexAI 来使用这些接口，而不需要单独导入每个模块。

从 code_utils 模块导入了 DEFAULT_MODEL 和 FAST_MODEL 两个变量。这两个变量可能是用于配置模型的参数。


"""

import logging
#from .version import __version__
#from .oai import *
#from .agentchat import *
#from .exception_utils import *
#from .code_utils import DEFAULT_MODEL, FAST_MODEL


"""
创建了一个名为 __name__ 的 logger 对象，并将其日志级别设置为 INFO。
__name__ 在这里是一个特殊的变量，它的值是当前模块的名字。
创建 logger 对象后，你就可以使用 logger.info(), logger.warning(), logger.error() 等方法来记录日志。
设置日志级别为 INFO 意味着 logger 会记录所有级别为 INFO 及以上的日志。

"""
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)