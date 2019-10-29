import requests
#url = '172.20.42.143:8080/MSAP/api/searchFlightInfo'
url = 'http://msap-bi.ceair.com:8080/MSAP/api/searchFlightInfo'
d = {'date':'2019-01-01','departureAirport':'PEK'}
r = requests.post(url, data=d)
print(r.text)
