#from flightradar24 import FlightRadar24API
import flightradar24
import pandas as pd
api = flightradar24.Api()
# 输出全部列
pd.set_option('display.max_columns', None)
# 获取机场列表
airports = api.get_airports()
#print(airports)
# 获取航班列表
flights = api.get_flight('fm863')
# 转换成dataframe
flight_data = flights["result"]["response"]["data"]
df = pd.json_normalize(flight_data)
print(df)

airline_code = 'AA'
airline_info = api.get_airlines()
# 转换成dataframe
airline_info = pd.DataFrame(airline_info)
print(airline_info)

