import requests
from bs4 import BeautifulSoup

def extract_info(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 提取公告信息
    announcements = soup.find_all('div', class_='sse_list_1')
    for announcement in announcements:
        title = announcement.find('a').text
        link = announcement.find('a')['href']
        print(f'Title: {title}, Link: {link}')

    # 提取PDF下载链接
    pdf_links = soup.find_all('a', href=True, text='PDF')
    for pdf_link in pdf_links:
        print(f'PDF Link: {pdf_link["href"]}')

extract_info('https://www.sse.com.cn/assortment/stock/list/info/company/index.shtml?COMPANY_CODE=600696')