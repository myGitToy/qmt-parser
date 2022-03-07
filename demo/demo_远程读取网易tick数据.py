import urllib.request
#根据url下载文件
#目前000数据可用 600数据无
#数据保存天数为
url = "http://quotes.money.163.com/cjmx/2021/20210625/1000333.xls"
downPath = '..\\000333_20210701.xls'#相对路径
urllib.request.urlretrieve(url,downPath)
