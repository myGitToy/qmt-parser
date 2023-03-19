import requests, re
all_codes = []
page = 1
while True:
    url = 'http://q.10jqka.com.cn/gn/detail/field/264648/order/desc/page/' + str(page) + '/ajax/1/code/309055/'
    response = requests.get(url)
    text = response.text
    #_blank">688387</a>
    pattern = r'\d{6}'
    codes = re.findall(pattern, text)
    all_codes.extend(codes)
    if '下一页' in text:
        page += 1
    else:
        break
print(all_codes)
