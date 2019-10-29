
# importing the requests library 
import requests 
  
# api-endpoint 
URL = "https://vpn.ceair.com/por/service.csp"
  
# location given here 
location = "delhi technological university"
  
# defining a params dict for the parameters to be sent to the API 
PARAMS = {'showsvc':1,'autoOpen':1,'rnd':'kohmdbhcplo'} 
  
# sending get request and saving the response as response object 
r = requests.get(url = URL, params = PARAMS) 
  
# extracting data in json format 
data = r.json() 
  