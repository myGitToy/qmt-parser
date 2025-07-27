#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
IPMI风扇控制脚本 - 浏览器自动化版本
适用于基于Web界面的现代BMC系统
"""

import time
import sys

# 检查是否安装了selenium
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException, WebDriverException
except ImportError:
    print("错误：需要安装selenium库")
    print("请运行：pip install selenium")
    print("还需要下载Chrome浏览器驱动 chromedriver.exe")
    sys.exit(1)

dic = {
    'username': 'admin',
    'password': 'admin',
    'ip': '192.168.1.170',
    'speed': '10',  # 需要调整的转速
    'fans': ["0", "1", "2", "3", "4", "5", "6", "7"],  # 需要调整转速的风扇端口
    'chrome_driver_path': 'chromedriver.exe',  # Chrome驱动路径
    'headless': False  # 是否无头模式运行
}

def create_driver():
    """创建Chrome浏览器驱动"""
    chrome_options = Options()
    
    # 忽略SSL证书错误
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument('--ignore-certificate-errors-spki-list')
    chrome_options.add_argument('--ignore-certificate-errors-certutils')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-insecure-localhost')
    
    # 其他选项
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    if dic['headless']:
        chrome_options.add_argument('--headless')
    
    try:
        # 尝试使用指定的驱动路径
        service = Service(dic['chrome_driver_path'])
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"使用指定驱动失败: {e}")
        try:
            # 尝试使用系统PATH中的驱动
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e2:
            print(f"创建浏览器驱动失败: {e2}")
            print("请确保：")
            print("1. 已安装Chrome浏览器")
            print("2. 下载了对应版本的chromedriver.exe")
            print("3. chromedriver.exe在脚本目录或系统PATH中")
            return None

def login_bmc(driver, ip, username, password):
    """登录BMC"""
    try:
        # 检测使用HTTP还是HTTPS
        protocols = ['https', 'http']
        for protocol in protocols:
            try:
                url = f"{protocol}://{ip}"
                print(f"尝试访问: {url}")
                driver.get(url)
                
                # 等待页面加载
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # 检查是否是登录页面
                if "login" in driver.current_url.lower() or "sign" in driver.current_url.lower():
                    print(f"成功访问登录页面: {driver.current_url}")
                    break
                    
                # 检查页面标题
                title = driver.title.lower()
                if "login" in title or "sign" in title or "management" in title:
                    print(f"找到登录页面: {driver.title}")
                    break
                    
            except Exception as e:
                print(f"访问 {protocol}://{ip} 失败: {e}")
                continue
        
        # 等待登录表单加载
        print("等待登录表单加载...")
        
        # 多种可能的用户名输入框选择器
        username_selectors = [
            "input[name='username']",
            "input[type='text']",
            "input[id*='user']",
            "input[id*='User']",
            "input[ng-model='username']",
            "#iduserName",
            "#username",
            "#user"
        ]
        
        username_element = None
        for selector in username_selectors:
            try:
                username_element = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                print(f"找到用户名输入框: {selector}")
                break
            except TimeoutException:
                continue
        
        if not username_element:
            print("未找到用户名输入框")
            return False
        
        # 多种可能的密码输入框选择器
        password_selectors = [
            "input[name='password']",
            "input[type='password']",
            "input[id*='pass']",
            "input[id*='Pass']",
            "input[ng-model='password']",
            "#password",
            "#pass"
        ]
        
        password_element = None
        for selector in password_selectors:
            try:
                password_element = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                print(f"找到密码输入框: {selector}")
                break
            except TimeoutException:
                continue
        
        if not password_element:
            print("未找到密码输入框")
            return False
        
        # 输入用户名和密码
        print("输入登录信息...")
        username_element.clear()
        username_element.send_keys(username)
        
        password_element.clear()
        password_element.send_keys(password)
        
        # 查找登录按钮
        login_button_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button[ng-click*='login']",
            "button[ng-click*='Login']",
            "button[ng-click*='doValidate']",
            "button.btn-success",
            "#loginBtn",
            "#login"
        ]
        
        login_button = None
        for selector in login_button_selectors:
            try:
                login_button = driver.find_element(By.CSS_SELECTOR, selector)
                if login_button.is_displayed() and login_button.is_enabled():
                    print(f"找到登录按钮: {selector}")
                    break
            except:
                continue
        
        if not login_button:
            print("未找到登录按钮")
            return False
        
        # 点击登录按钮
        print("点击登录按钮...")
        login_button.click()
        
        # 等待登录完成
        print("等待登录完成...")
        time.sleep(3)
        
        # 检查是否登录成功
        current_url = driver.current_url
        if "main" in current_url.lower() or "dashboard" in current_url.lower() or "home" in current_url.lower():
            print("登录成功！")
            return True
        
        # 检查是否有错误信息
        error_selectors = [
            ".alert-danger",
            ".error",
            ".alert-error",
            "[ng-show*='error']"
        ]
        
        for selector in error_selectors:
            try:
                error_element = driver.find_element(By.CSS_SELECTOR, selector)
                if error_element.is_displayed():
                    print(f"登录错误: {error_element.text}")
                    return False
            except:
                continue
        
        print("登录状态未知，请检查页面")
        return False
        
    except Exception as e:
        print(f"登录过程中发生错误: {e}")
        return False

def find_fan_control_page(driver):
    """查找风扇控制页面"""
    try:
        # 可能的风扇控制页面链接文本
        fan_links = [
            "Fan Control",
            "风扇控制",
            "Cooling",
            "散热",
            "Thermal",
            "Hardware",
            "硬件",
            "Sensors",
            "传感器"
        ]
        
        print("查找风扇控制页面...")
        
        # 尝试点击导航菜单
        for link_text in fan_links:
            try:
                link = driver.find_element(By.PARTIAL_LINK_TEXT, link_text)
                if link.is_displayed():
                    print(f"找到风扇控制链接: {link_text}")
                    link.click()
                    time.sleep(2)
                    return True
            except:
                continue
        
        # 尝试直接访问可能的URL
        possible_urls = [
            "/fan",
            "/fan.html",
            "/fan_control",
            "/thermal",
            "/cooling",
            "/hardware",
            "/sensors"
        ]
        
        base_url = driver.current_url.split('/', 3)[0:3]
        base_url = '/'.join(base_url)
        
        for url in possible_urls:
            try:
                full_url = base_url + url
                print(f"尝试访问: {full_url}")
                driver.get(full_url)
                time.sleep(2)
                
                # 检查页面内容
                if "fan" in driver.page_source.lower() or "cooling" in driver.page_source.lower():
                    print("找到风扇控制页面！")
                    return True
            except:
                continue
        
        print("未找到风扇控制页面")
        return False
        
    except Exception as e:
        print(f"查找风扇控制页面时发生错误: {e}")
        return False

def main():
    print("感谢使用IPMI风扇控制脚本 - 浏览器自动化版本")
    print('—' * 60)
    
    # 创建浏览器驱动
    driver = create_driver()
    if not driver:
        return
    
    try:
        # 登录BMC
        if not login_bmc(driver, dic['ip'], dic['username'], dic['password']):
            print("登录失败")
            return
        
        # 查找风扇控制页面
        if not find_fan_control_page(driver):
            print("未找到风扇控制页面")
            print("请手动导航到风扇控制页面，然后按回车键继续...")
            input()
        
        print("已准备好进行风扇控制操作")
        print("当前页面URL:", driver.current_url)
        print("请在浏览器中手动完成风扇速度调整，或者按回车键退出")
        input()
        
    except Exception as e:
        print(f"操作过程中发生错误: {e}")
    
    finally:
        # 关闭浏览器
        if not dic['headless']:
            print("按回车键关闭浏览器...")
            input()
        driver.quit()

if __name__ == "__main__":
    main()
