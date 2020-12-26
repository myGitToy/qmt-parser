from apt.os.data_tick import Data_tick
import datetime

a = Data_tick()
start = datetime.datetime(2020,12,16)
a.update_v2(start_date = start)
#df = a.get_tick_data(code = '000001' , day='2020-01-07')
