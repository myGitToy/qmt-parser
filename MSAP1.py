import urllib.parse
import urllib.request

url =  'http://msap-bi.ceair.com:8080/MSAP/api/searchFlightInfo'
values = {'date':'2019-01-01','departureAirport':'PEK'}
data = urllib.parse.urlencode(values)
data = data.encode('ascii') # data should be bytes
req = urllib.request.Request(url, data)
with urllib.request.urlopen(req) as response:
   the_page = response.read()