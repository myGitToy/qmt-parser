from apt.os.data_tick import Data_tick
import datetime

a = Data_tick()
start = datetime.datetime(2021,2,9)
end = datetime.datetime(2021,2,22)
a.update_v2(start_date = start , end_date = end)
#df = a.get_tick_data(code = '000001' , day='2020-01-07')
