import pandas as pd
import tushare as ts
from apt.qsp_universal.base import base as data
from apt.vendor.tspro.data import data as tspro_data

class finance(tspro_data):
    def __init__(self):
        super().__init__()