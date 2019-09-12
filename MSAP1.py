import urllib.request
import urllib.parse
url = 'http://172.20.42.143:8080/MSAP/api/searchFlightInfo?date=2019-09-01&departureAirport=PEK'
f = urllib.request.urlopen(url)
print(f.read().decode('utf-8'))
