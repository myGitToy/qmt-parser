import numpy as np
import pandas as pd
import tushare as ts
from datetime import datetime,timedelta
from apt.vendor.tspro.security import security  as security
from apt.vendor.tspro.data import data as data
from apt.vendor.tspro.base import base as base
#1. 更新序列
a = data(myauth = True,rds_host = base.数据源.centos9)
#优先更新高权限序列
a.update_sequence_launch(priority = 1)
a.update_sequence_launch(priority = 0)

