#from flightradar24 import FlightRadar24API
import flightradar24
api = flightradar24.Api()
# 获取机场列表
airports = api.get_airports()
#print(airports)
# 获取航班列表
flights = api.get_flight('fm863')
print(flights)
airline_code = 'AA'
airline_info = api.get_airlines()
#print(airline_info)

