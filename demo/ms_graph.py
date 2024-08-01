import requests
import msal

# Azure应用程序的配置信息
CLIENT_ID = 'your_client_id'
CLIENT_SECRET = 'your_client_secret'
TENANT_ID = 'your_tenant_id'
AUTHORITY = f'https://login.microsoftonline.com/{TENANT_ID}'
SCOPE = ['https://graph.microsoft.com/.default']

# 获取访问令牌
app = msal.ConfidentialClientApplication(CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET)
result = app.acquire_token_for_client(scopes=SCOPE)

if 'access_token' in result:
    access_token = result['access_token']
else:
    raise Exception('获取访问令牌失败')

# 使用访问令牌读取OneNote内容
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

# 获取用户的笔记本列表
notebooks_url = 'https://graph.microsoft.com/v1.0/me/onenote/notebooks'
response = requests.get(notebooks_url, headers=headers)
notebooks = response.json()

# 打印笔记本列表
for notebook in notebooks['value']:
    print(f"Notebook: {notebook['displayName']}")

    # 获取笔记本中的分区
    sections_url = notebook['sectionsUrl']
    response = requests.get(sections_url, headers=headers)
    sections = response.json()

    for section in sections['value']:
        print(f"  Section: {section['displayName']}")

        # 获取分区中的页面
        pages_url = section['pagesUrl']
        response = requests.get(pages_url, headers=headers)
        pages = response.json()

        for page in pages['value']:
            print(f"    Page: {page['title']}")
            print(f"    Page Content URL: {page['contentUrl']}")