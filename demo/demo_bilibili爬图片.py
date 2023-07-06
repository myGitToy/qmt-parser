import requests
from bs4 import BeautifulSoup
#from selenium import webdriver

# 创建一个Chrome浏览器实例
#driver = webdriver.Chrome()
# 访问指定的网址
#driver.get('https://t.bilibili.com/756610458525368370?spm_id_from=333.999.0.0')

# 获取网页内容
#content = driver.page_source

# 关闭浏览器
#driver.close()
# 发起网络请求，获取HTML页面
response = requests.get('https://t.bilibili.com/756610458525368370?spm_id_from=333.999.0.0')

# 使用BeautifulSoup解析HTML页面
soup = BeautifulSoup(response.text, 'html.parser')

# 找到所有图片链接
image_tags = soup.find_all('img')

# 遍历图片链接，下载图片
for image_tag in image_tags:
    image_url = image_tag['src']
    response = requests.get(image_url)
    with open('image.jpg', 'wb') as f:
        f.write(response.content)
