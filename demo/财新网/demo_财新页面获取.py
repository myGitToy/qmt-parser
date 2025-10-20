import undetected_chromedriver as uc
from selenium import webdriver
import time
import requests
from bs4 import BeautifulSoup
import os
import re
import json
import datetime

def get_caixin_cookies(headless=False, login_check=True):
    """
    获取财新网的 cookies
    
    参数:
        headless: 是否使用无头模式
        login_check: 是否检查登录状态
    """
    url = "https://www.caixin.com/"  # 财新网首页
    
    # 使用 undetected-chromedriver (推荐，反爬能力更强)
    options = uc.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    # 如果需要有界面浏览器，请设置headless=False
    if headless:
        options.add_argument("--headless=new")
    
    print(f"正在启动浏览器{'(无头模式)' if headless else '(有界面模式)'}")
    driver = uc.Chrome(options=options)
    
    try:
        print(f"正在访问: {url}")
        driver.get(url)
        
        # 等待用户手动登录 (关闭headless模式使用)
        if not headless:
            print("请在浏览器中登录财新网...")
            input("登录完成后按回车继续...")
        else:
            # 如果是无头模式，可以适当等待一下让页面加载
            time.sleep(3)
        
        # 检查是否已登录
        if login_check:
            # 检查页面上是否有登录状态的元素
            try:
                # 等待一下，确保页面元素加载完毕
                time.sleep(2)
                
                # 尝试查找登录状态元素 (可能是用户名或"我的财新"之类的元素)
                login_elements = driver.find_elements("xpath", "//*[contains(text(), '我的财新') or contains(@class, 'user-name') or contains(@class, 'login-info')]")
                
                if login_elements:
                    print("检测到登录状态元素，似乎已成功登录")
                    for elem in login_elements[:2]:  # 只打印前两个匹配元素
                        print(f"- 找到登录状态元素: {elem.text if elem.text else '[无文本]'}")
                else:
                    print("警告：未检测到登录状态元素，可能未成功登录")
                    if not headless:
                        retry = input("是否需要重试登录? (y/n): ")
                        if retry.lower() == 'y':
                            input("请在浏览器中完成登录，然后按回车继续...")
            except Exception as e:
                print(f"检查登录状态时出错: {e}")
        
        # 获取所有cookies
        cookies_list = driver.get_cookies()
        print(f"获取到 {len(cookies_list)} 个cookies")
        
        # 打印一些重要的cookie进行调试
        important_cookies = ["auth", "token", "user", "session", "login"]
        found_important = False
        for cookie in cookies_list:
            for keyword in important_cookies:
                if keyword in cookie['name'].lower():
                    print(f"找到重要cookie: {cookie['name']} = {cookie['value'][:5]}...")
                    found_important = True
        
        if not found_important:
            print("警告：未找到典型的登录相关cookie，可能未成功登录")
        
        # 转换为字典格式
        cookies_dict = {}
        for cookie in cookies_list:
            cookies_dict[cookie['name']] = cookie['value']
        
        # 转换为字符串格式 (name=value; name2=value2)
        cookies_str = "; ".join([f"{name}={value}" for name, value in cookies_dict.items()])
        
        return cookies_dict, cookies_str
    
    finally:
        driver.quit()
        print("浏览器已关闭")

def get_caixin_article(url, cookies_str):
    """使用cookies访问财新网文章并获取正文内容"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Cookie": cookies_str,
        "Referer": "https://www.caixin.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    print(f"正在访问文章: {url}")
    print(f"Cookie长度: {len(cookies_str)} 字符")
    # 打印Cookie的前100个字符作为参考
    if len(cookies_str) > 100:
        print(f"Cookie预览: {cookies_str[:100]}...")
    else:
        print(f"Cookie内容: {cookies_str}")
        
    # 先不带Cookie请求一次，获取非登录状态内容
    print("首先不带Cookie请求一次，获取非登录状态的内容...")
    headers_no_cookie = headers.copy()
    del headers_no_cookie["Cookie"]
    response_no_cookie = requests.get(url, headers=headers_no_cookie)
    response_no_cookie.encoding = 'utf-8'
    
    # 然后带Cookie请求
    print("带Cookie请求...")
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'  # 确保中文正常显示
    
    if response.status_code != 200:
        print(f"访问失败，状态码: {response.status_code}")
        return None, None
        
    # 比较两次请求的响应长度
    print(f"非登录状态响应长度: {len(response_no_cookie.text)} 字符")
    print(f"带Cookie响应长度: {len(response.text)} 字符")
    
    # 检查响应是否包含付费墙特征
    if "需要付费才能阅读" in response.text or "付费订阅" in response.text:
        print("警告：检测到付费墙，Cookie可能无效或权限不足")
    
    # 检查两次响应是否有差异
    if len(response.text) == len(response_no_cookie.text):
        print("警告：带Cookie和不带Cookie的响应长度相同，Cookie可能无效")
    elif len(response.text) > len(response_no_cookie.text):
        print("Cookie似乎有效：带Cookie的响应更长")
    else:
        print("警告：不带Cookie的响应更长，这很不寻常")
    
    # 保存HTML以便调试
    with open("caixin_article_debug.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("已保存HTML到caixin_article_debug.html文件，供调试")
    
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 提取标题
    title = soup.find('h1')
    title_text = title.text.strip() if title else "无法获取标题"
    print(f"找到标题: {title_text}")
    
    # 查找财新网文章正文的多种可能的CSS选择器
    content_div = None
    possible_selectors = [
        "div.article-content", 
        "div.text",  # 另一个可能的选择器
        "div.content",  # 另一个可能的选择器
        "article.article-content",  # 可能是article标签
        "div.ystyle"  # 财新网可能使用的另一个类名
    ]
    
    # 尝试不同的选择器
    for selector in possible_selectors:
        print(f"尝试选择器: {selector}")
        if "." in selector:
            tag, class_name = selector.split(".")
            content_div = soup.find(tag, class_=class_name)
        else:
            content_div = soup.find(selector)
            
        if content_div:
            print(f"使用选择器 {selector} 找到了内容")
            break
    
    if not content_div:
        print("未找到文章正文，尝试使用更通用的方法...")
        # 尝试一种更通用的方法 - 查找所有可能包含文章内容的大段文本
        article_divs = soup.find_all('div', class_=lambda c: c and ('article' in c or 'content' in c or 'text' in c))
        
        if article_divs:
            print(f"找到 {len(article_divs)} 个可能的内容区域")
            # 选择包含最多<p>标签的div作为正文
            content_div = max(article_divs, key=lambda div: len(div.find_all('p')))
        else:
            print("未找到任何可能的文章内容区域")
            return title_text, None
    
    # 尝试多种方式提取文本
    content = ""
    # 1. 首先尝试提取所有段落
    paragraphs = content_div.find_all('p')
    if paragraphs:
        content = "\n\n".join([p.text.strip() for p in paragraphs])
    else:
        # 2. 如果没有<p>标签，直接获取所有文本
        content = content_div.get_text(separator="\n\n")
    
    if not content.strip():
        print("提取的内容为空")
        return title_text, None
    
    print(f"成功获取文章: {title_text} (内容长度: {len(content)} 字符)")
    return title_text, content

def save_article_to_file(title, content, folder="articles"):
    """将文章保存到文件"""
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    # 生成安全的文件名
    safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)
    filename = os.path.join(folder, f"{safe_title}.txt")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"标题: {title}\n\n")
        f.write(content)
    
    print(f"文章已保存至: {filename}")
    return filename

def save_cookies(cookies_list, filename="caixin_cookies.json"):
    """保存cookie到文件"""
    # 为cookie添加时间戳
    cookie_data = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cookies": cookies_list
    }
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(cookie_data, f, ensure_ascii=False, indent=2)
    
    print(f"Cookie已保存至: {filename}")
    return filename

def load_cookies(filename="caixin_cookies.json"):
    """从文件加载cookie"""
    if not os.path.exists(filename):
        print(f"Cookie文件 {filename} 不存在")
        return None, None
        
    try:
        with open(filename, "r", encoding="utf-8") as f:
            cookie_data = json.load(f)
            
        # 计算cookie的年龄
        timestamp = datetime.datetime.strptime(cookie_data["timestamp"], "%Y-%m-%d %H:%M:%S")
        age = datetime.datetime.now() - timestamp
        
        print(f"已加载Cookie, 保存时间: {cookie_data['timestamp']} (距今 {age.days} 天 {age.seconds//3600} 小时)")
        
        cookies_list = cookie_data["cookies"]
        
        # 转换为字典格式
        cookies_dict = {}
        for cookie in cookies_list:
            if "name" in cookie and "value" in cookie:  # 确保cookie格式正确
                cookies_dict[cookie["name"]] = cookie["value"]
        
        # 转换为字符串格式
        cookies_str = "; ".join([f"{name}={value}" for name, value in cookies_dict.items()])
        
        return cookies_list, cookies_str
    except Exception as e:
        print(f"加载Cookie出错: {e}")
        return None, None

# 尝试使用浏览器获取内容的函数
def get_caixin_article_with_browser(url, headless=False):
    """使用浏览器获取财新网文章内容（用于应对复杂的动态内容）"""
    options = uc.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    if headless:
        options.add_argument("--headless=new")
    
    print(f"正在启动浏览器{'(无头模式)' if headless else '(有界面模式)'}来获取文章内容")
    driver = uc.Chrome(options=options)
    
    try:
        print(f"正在访问文章: {url}")
        driver.get(url)
        
        # 等待页面加载
        time.sleep(5)  # 给JavaScript足够的时间执行
        
        # 获取标题
        try:
            title_element = driver.find_element("tag name", "h1")
            title = title_element.text.strip()
        except:
            title = "无法获取标题"
        
        print(f"找到标题: {title}")
        
        # 获取页面HTML
        page_source = driver.page_source
        
        # 保存HTML以便调试
        with open("caixin_article_browser_debug.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        
        # 使用BeautifulSoup解析
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # 尝试多种选择器
        content_div = None
        for selector in ["div.article-content", "div.text", "div.content", "article.article-content", "div.ystyle"]:
            if "." in selector:
                tag, class_name = selector.split(".")
                content_div = soup.find(tag, class_=class_name)
            else:
                content_div = soup.find(selector)
                
            if content_div:
                break
        
        if not content_div:
            # 尝试更通用的方法
            article_divs = soup.find_all('div', class_=lambda c: c and ('article' in c or 'content' in c or 'text' in c))
            if article_divs:
                content_div = max(article_divs, key=lambda div: len(div.find_all('p')))
            else:
                return title, None
        
        # 提取内容
        paragraphs = content_div.find_all('p')
        if paragraphs:
            content = "\n\n".join([p.text.strip() for p in paragraphs])
        else:
            content = content_div.get_text(separator="\n\n")
        
        return title, content
        
    finally:
        driver.quit()
        print("浏览器已关闭")

def get_caixin_article_with_login_browser(url, cookies_list=None):
    """
    使用已登录的浏览器直接获取文章内容
    
    参数:
        url: 文章URL
        cookies_list: 可选的cookies列表
    """
    options = uc.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    print("正在启动浏览器(有界面模式)来直接访问文章")
    driver = uc.Chrome(options=options)
    
    try:
        # 如果提供了cookies，先应用cookies
        if cookies_list:
            # 首先访问网站主域名
            domain = url.split("/")[2]
            base_url = f"https://{domain}"
            print(f"正在访问基础域名: {base_url} 以设置cookies")
            driver.get(base_url)
            time.sleep(2)
            
            # 添加cookies
            print(f"添加 {len(cookies_list)} 个cookies到浏览器")
            for cookie in cookies_list:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    print(f"添加cookie失败: {e}")
            
            # 刷新页面使cookies生效
            driver.refresh()
            time.sleep(2)
        else:
            print("未提供cookies，请在打开的浏览器中手动登录")
        
        # 访问文章页面
        print(f"正在访问文章: {url}")
        driver.get(url)
        
        # 等待用户手动登录或确认
        input("请在必要时在浏览器中登录，然后按回车继续...")
        
        # 获取页面内容
        title_element = driver.find_element("tag name", "h1")
        title = title_element.text.strip() if title_element else "无法获取标题"
        
        # 保存HTML以便调试
        page_source = driver.page_source
        with open("caixin_article_login_browser_debug.html", "w", encoding="utf-8") as f:
            f.write(page_source)
            
        # 解析内容
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # 尝试多种选择器找到内容
        content_div = None
        for selector in ["div.article-content", "div.text", "div.content", "article.article-content", "div.ystyle"]:
            if "." in selector:
                tag, class_name = selector.split(".")
                content_div = soup.find(tag, class_=class_name)
            else:
                content_div = soup.find(selector)
                
            if content_div:
                break
                
        if not content_div:
            article_divs = soup.find_all('div', class_=lambda c: c and ('article' in c or 'content' in c or 'text' in c))
            if article_divs:
                content_div = max(article_divs, key=lambda div: len(div.find_all('p')))
        
        # 提取内容
        if content_div:
            paragraphs = content_div.find_all('p')
            if paragraphs:
                content = "\n\n".join([p.text.strip() for p in paragraphs])
            else:
                content = content_div.get_text(separator="\n\n")
            return title, content
        else:
            return title, None
            
    finally:
        # 保存最终的cookies以备后用
        final_cookies = driver.get_cookies()
        print(f"浏览器最终有 {len(final_cookies)} 个cookies")
        driver.quit()
        print("浏览器已关闭")
        return final_cookies

# 使用示例
if __name__ == "__main__":
    import argparse
    
    # 定义命令行参数
    parser = argparse.ArgumentParser(description='财新网文章获取工具')
    parser.add_argument('--url', type=str, help='要获取的文章URL', 
                        default="https://economy.caixin.com/2025-10-20/102373425.html")
    parser.add_argument('--mode', type=str, choices=['login', 'saved', 'browser'], 
                        default='saved', help='工作模式: login(重新登录), saved(使用保存的cookie), browser(使用浏览器)')
    parser.add_argument('--cookie-file', type=str, default='caixin_cookies.json', 
                        help='Cookie保存/加载文件路径')
    
    # 解析命令行参数
    args = parser.parse_args()
    article_url = args.url
    mode = args.mode
    cookie_file = args.cookie_file
    
    print(f"财新网文章获取工具启动")
    print(f"目标文章: {article_url}")
    print(f"工作模式: {mode}")
    print(f"Cookie文件: {cookie_file}")
    
    # 根据不同模式处理
    if mode == 'login':
        # 浏览器手动登录模式
        print("\n===== 浏览器手动登录模式 =====")
        try:
            # 使用浏览器打开，让用户手动登录
            cookies_dict, cookies_str = get_caixin_cookies(headless=False, login_check=True)
            print("登录成功，获取到Cookie")
            
            # 获取完整的cookie列表
            options = uc.ChromeOptions()
            driver = uc.Chrome(options=options)
            driver.get("https://www.caixin.com/")
            time.sleep(1)
            # 给用户一个提示，确认是否已经登录
            input("请确认您在浏览器中已经登录成功，然后按回车继续...")
            cookies_list = driver.get_cookies()
            driver.quit()
            
            # 保存cookie到文件
            save_cookies(cookies_list, cookie_file)
            
            # 使用获取的cookie访问文章
            print("使用新获取的cookie访问文章...")
            title, content = get_caixin_article(article_url, cookies_str)
            
            if content:
                print(f"获取成功，内容长度: {len(content)} 字符")
                # 保存文章
                save_article_to_file(title, content)
            else:
                print("获取文章失败，尝试使用浏览器直接访问")
                final_cookies = get_caixin_article_with_login_browser(article_url, cookies_list)
                # 保存最新的cookie
                save_cookies(final_cookies, cookie_file)
        except Exception as e:
            print(f"登录模式出错: {e}")
            
    elif mode == 'saved':
        # 使用保存的cookie模式
        print("\n===== 使用保存的Cookie模式 =====")
        try:
            # 尝试加载保存的cookie
            cookies_list, cookies_str = load_cookies(cookie_file)
            
            if cookies_list:
                print("成功加载保存的cookie")
                # 使用加载的cookie访问文章
                print("使用保存的cookie访问文章...")
                title, content = get_caixin_article(article_url, cookies_str)
                
                if content:
                    print(f"获取成功，内容长度: {len(content)} 字符")
                    # 保存文章
                    save_article_to_file(title, content)
                else:
                    print("使用保存的cookie获取文章失败")
                    print("可能需要重新登录，请使用 --mode login 参数运行")
                    
                    retry = input("是否要切换到登录模式重试? (y/n): ")
                    if retry.lower() == 'y':
                        # 切换到登录模式
                        cookies_dict, cookies_str = get_caixin_cookies(headless=False, login_check=True)
                        options = uc.ChromeOptions()
                        driver = uc.Chrome(options=options)
                        driver.get("https://www.caixin.com/")
                        time.sleep(1)
                        input("请确认您在浏览器中已经登录成功，然后按回车继续...")
                        cookies_list = driver.get_cookies()
                        driver.quit()
                        
                        # 保存新cookie
                        save_cookies(cookies_list, cookie_file)
                        
                        # 使用新cookie重试
                        print("使用新cookie重试...")
                        title, content = get_caixin_article(article_url, cookies_str)
                        if content:
                            print(f"重试成功，内容长度: {len(content)} 字符")
                            save_article_to_file(title, content)
            else:
                print("未找到有效的保存cookie或cookie加载失败")
                print("需要首次登录，请使用 --mode login 参数运行")
        except Exception as e:
            print(f"使用保存cookie模式出错: {e}")
            
    else:  # browser模式
        # 直接使用浏览器访问
        print("\n===== 直接使用浏览器访问模式 =====")
        try:
            # 尝试加载保存的cookie
            cookies_list, _ = load_cookies(cookie_file)
            
            # 直接使用浏览器访问文章
            print("使用浏览器直接访问文章...")
            final_cookies = get_caixin_article_with_login_browser(article_url, cookies_list)
            
            # 保存最新的cookie
            if final_cookies:
                save_cookies(final_cookies, cookie_file)
                
        except Exception as e:
            print(f"浏览器访问模式出错: {e}")