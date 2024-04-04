import urllib.request
impots
from bs4 import BeautifulSoup as bs

url = "https://zh.taotu.org/hot-girls/%e5%b0%8f%e8%94%a1%e5%a4%b4%e5%96%b5%e5%96%b5%e5%96%b5/00062-%e8%af%95%e8%a1%a3%e9%97%b42-84p/"
soup = bs(urllib.request.urlopen(url))
parsed = list(urllib.request.urlparse(url))

out_folder = "C:\\img_download\\" 

for image in soup.findAll("img"):
  print("Image: % (src)s" % image)
  image_url = urllib.request.urljoin(url, image["src"])
  filename = image["src"].split("/")[-1]
  outpath = os.path.join(out_folder, filename)
  urllib.request.urlretrieve(image_url, outpath)
