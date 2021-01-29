from apt.os.data_tick import Data_tick
import datetime

a = Data_tick()
start = datetime.datetime(2021,1,8)
end = datetime.datetime(2021,1,29)
a.update_v2(start_date = start)
#df = a.get_tick_data(code = '000001' , day='2020-01-07')
