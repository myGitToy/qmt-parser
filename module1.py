from datetime import datetime,timedelta
import numpy as np
import pandas as pd
import tushare as ts
import logging
import os

print(ts.get_k_data('501041', ktype='60'))
