import urllib.request
from bs4 import BeautifulSoup as bs

url = "https://zh.taotu.org/xiuren/04936-xiuren-no-4985-tang-anqi-beige-suspender-dress-with-light-gray-stockings/"
soup = bs(urllib.request.urlopen(url))
parsed = list(urllib.request.urlparse(url))

out_folder = "D:\\img_download\\" 

for image in soup.findAll("img"):
  print("Image: % (src)s" % image)
  image_url = urllib.request.urljoin(url, image["src"])
  filename = image["src"].split("/")[-1]
  outpath = os.path.join(out_folder, filename)
  urllib.request.urlretrieve(image_url, outpath)
