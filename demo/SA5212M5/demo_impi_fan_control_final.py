#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
IPMI风扇控制脚本 - 最终解决方案
分析JavaScript登录流程并模拟真实的登录过程
"""

import http.client
import ssl
import re
import socket
import time
import json
import hashlib
import base64
import urllib.parse

dic = {
    'username': 'admin',
    'password': 'admin',
    'ip': '192.168.1.170',
    'speed': '10',
    'fans': ["0", "1", "2", "3", "4", "5", "6", "7"]
}

class BMCClient:
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password
        self.conn = None
        self.session_token = None
        self.protocol = None
        
    def create_connection(self):
        """创建连接"""
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            self.conn = http.client.HTTPSConnection(self.ip, 443, context=context, timeout=30)
            self.protocol = "https"
            
            # 测试连接
            self.conn.request("GET", "/", "", {})
            response = self.conn.getresponse()
            response.read()
            
            print(f"使用HTTPS连接到 {self.ip}")
            return True
            
        except Exception as e:
            print(f"HTTPS连接失败: {e}")
            try:
                self.conn = http.client.HTTPConnection(self.ip, 80, timeout=30)
                self.protocol = "http"
                
                # 测试连接
                self.conn.request("GET", "/", "", {})
                response = self.conn.getresponse()
                response.read()
                
                print(f"使用HTTP连接到 {self.ip}")
                return True
                
            except Exception as e2:
                print(f"HTTP连接也失败: {e2}")
                return False
    
    def get_js_files(self):
        """获取JavaScript文件内容"""
        try:
            print("获取JavaScript文件...")
            js_files = ['js/signin.js', 'js/Blowfish.js', 'lib/ui.js']
            js_content = {}
            
            for js_file in js_files:
                try:
                    self.conn.request("GET", f"/{js_file}", "", {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    response = self.conn.getresponse()
                    if response.status == 200:
                        content = response.read().decode('utf-8')
                        js_content[js_file] = content
                        print(f"成功获取 {js_file} ({len(content)} 字符)")
                    else:
                        print(f"获取 {js_file} 失败: {response.status}")
                except Exception as e:
                    print(f"获取 {js_file} 异常: {e}")
            
            return js_content
            
        except Exception as e:
            print(f"获取JavaScript文件失败: {e}")
            return {}
    
    def analyze_login_process(self, js_content):
        """分析登录过程"""
        try:
            print("分析登录流程...")
            
            # 查找登录相关的函数和端点
            login_patterns = [
                r'function\s+(\w*[Ll]ogin\w*)\s*\(',
                r'(\w*[Ll]ogin\w*)\s*:\s*function',
                r'(doValidate|validate|submit)\s*:\s*function',
                r'url\s*:\s*["\']([^"\']*(?:login|auth|session)[^"\']*)["\']',
                r'post\s*\(\s*["\']([^"\']*)["\']',
                r'\.post\s*\(\s*["\']([^"\']*)["\']'
            ]
            
            endpoints = set()
            functions = set()
            
            for js_file, content in js_content.items():
                for pattern in login_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            for m in match:
                                if m and ('/' in m or m.startswith('/') or 'login' in m.lower()):
                                    endpoints.add(m)
                                elif m:
                                    functions.add(m)
                        elif match and ('/' in match or match.startswith('/') or 'login' in match.lower()):
                            endpoints.add(match)
                        elif match:
                            functions.add(match)
            
            print(f"找到可能的登录端点: {list(endpoints)}")
            print(f"找到可能的登录函数: {list(functions)}")
            
            # 查找密码加密方法
            encryption_patterns = [
                r'(blowfish|encrypt|hash|md5|sha)',
                r'password\s*=\s*([^;]+)',
                r'encrypt\s*\([^)]+\)',
                r'Blowfish\s*\([^)]+\)'
            ]
            
            encryption_methods = set()
            for js_file, content in js_content.items():
                for pattern in encryption_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        encryption_methods.add(match)
            
            print(f"找到可能的加密方法: {list(encryption_methods)}")
            
            return list(endpoints), list(functions), list(encryption_methods)
            
        except Exception as e:
            print(f"分析登录过程失败: {e}")
            return [], [], []
    
    def try_encrypted_login(self, endpoints):
        """尝试加密登录"""
        try:
            print("尝试加密登录...")
            
            # 尝试不同的加密方式
            encryption_methods = [
                ('base64', lambda x: base64.b64encode(x.encode()).decode()),
                ('md5', lambda x: hashlib.md5(x.encode()).hexdigest()),
                ('sha256', lambda x: hashlib.sha256(x.encode()).hexdigest()),
                ('plain', lambda x: x)
            ]
            
            for endpoint in endpoints:
                if not endpoint.startswith('/'):
                    endpoint = '/' + endpoint
                    
                for enc_name, enc_func in encryption_methods:
                    try:
                        encrypted_password = enc_func(self.password)
                        
                        # 尝试不同的参数名
                        param_variations = [
                            f"username={self.username}&password={encrypted_password}",
                            f"user={self.username}&pass={encrypted_password}",
                            f"login={self.username}&password={encrypted_password}",
                            f"WEBVAR_USERNAME={self.username}&WEBVAR_PASSWORD={encrypted_password}",
                            json.dumps({"username": self.username, "password": encrypted_password}),
                            json.dumps({"user": self.username, "pass": encrypted_password})
                        ]
                        
                        for payload in param_variations:
                            headers = {
                                'Content-Type': 'application/x-www-form-urlencoded' if not payload.startswith('{') else 'application/json',
                                'Accept': 'application/json, text/plain, */*',
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                                'Origin': f'{self.protocol}://{self.ip}',
                                'Referer': f'{self.protocol}://{self.ip}/'
                            }
                            
                            print(f"尝试端点: {endpoint}, 加密: {enc_name}, 参数: {payload[:50]}...")
                            
                            self.conn.request("POST", endpoint, payload, headers)
                            response = self.conn.getresponse()
                            response_data = response.read()
                            
                            try:
                                response_text = response_data.decode('utf-8')
                            except:
                                response_text = str(response_data)
                            
                            print(f"状态码: {response.status}")
                            
                            # 检查是否登录成功
                            if response.status == 200:
                                # 检查JSON响应
                                try:
                                    json_data = json.loads(response_text)
                                    if 'success' in json_data and json_data['success']:
                                        if 'token' in json_data:
                                            self.session_token = json_data['token']
                                            print(f"登录成功! Token: {self.session_token}")
                                            return True
                                        elif 'session' in json_data:
                                            self.session_token = json_data['session']
                                            print(f"登录成功! Session: {self.session_token}")
                                            return True
                                except:
                                    pass
                                
                                # 检查Set-Cookie头
                                for header_name, header_value in response.getheaders():
                                    if header_name.lower() == 'set-cookie':
                                        if 'session' in header_value.lower():
                                            cookie_match = re.search(r'([^=]+)=([^;]+)', header_value)
                                            if cookie_match:
                                                self.session_token = cookie_match.group(2)
                                                print(f"登录成功! 从Cookie获取: {self.session_token}")
                                                return True
                                
                                # 检查是否重定向到主页面
                                if response.status == 302:
                                    location = response.getheader('Location')
                                    if location and ('main' in location or 'home' in location or 'dashboard' in location):
                                        print("登录成功! 检测到重定向到主页面")
                                        return True
                            
                            time.sleep(0.5)  # 避免请求过快
                            
                    except Exception as e:
                        print(f"尝试 {endpoint} 和 {enc_name} 失败: {e}")
                        continue
            
            return False
            
        except Exception as e:
            print(f"加密登录失败: {e}")
            return False
    
    def analyze_and_login(self):
        """分析并登录"""
        try:
            if not self.create_connection():
                return False
            
            # 获取JavaScript文件
            js_content = self.get_js_files()
            if not js_content:
                print("无法获取JavaScript文件，使用默认端点")
                endpoints = ['/rpc/WEBSES/create.asp', '/api/login', '/login']
            else:
                # 分析登录过程
                endpoints, functions, encryption_methods = self.analyze_login_process(js_content)
                if not endpoints:
                    endpoints = ['/rpc/WEBSES/create.asp', '/api/login', '/login']
            
            # 尝试登录
            if self.try_encrypted_login(endpoints):
                return True
            
            print("所有登录尝试都失败了")
            return False
            
        except Exception as e:
            print(f"登录分析失败: {e}")
            return False
    
    def control_fans(self):
        """控制风扇"""
        if not self.session_token:
            print("没有有效的session token")
            return False
        
        try:
            print("尝试控制风扇...")
            
            # 风扇控制端点
            fan_endpoints = [
                '/rpc/setfanmode.asp',
                '/api/fan/mode',
                '/fan/mode',
                '/rpc/setfanspeed.asp',
                '/api/fan/speed',
                '/fan/speed'
            ]
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json, text/plain, */*',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Origin': f'{self.protocol}://{self.ip}',
                'Referer': f'{self.protocol}://{self.ip}/main.html',
                'Cookie': f'SessionCookie={self.session_token}; Username={self.username}'
            }
            
            # 设置风扇为手动模式
            for endpoint in fan_endpoints:
                if 'mode' in endpoint:
                    try:
                        self.conn.request("POST", endpoint, "MODE=1", headers)
                        response = self.conn.getresponse()
                        response_data = response.read()
                        
                        print(f"设置风扇模式端点 {endpoint}: {response.status}")
                        if response.status == 200:
                            print("风扇设置为手动模式成功")
                            break
                    except Exception as e:
                        print(f"设置风扇模式失败: {e}")
            
            # 设置风扇转速
            for endpoint in fan_endpoints:
                if 'speed' in endpoint:
                    try:
                        for fan_id in dic['fans']:
                            payload = f"ID={fan_id}&PERCENT={dic['speed']}"
                            self.conn.request("POST", endpoint, payload, headers)
                            response = self.conn.getresponse()
                            response_data = response.read()
                            
                            print(f"设置风扇{fan_id}转速: {response.status}")
                            if response.status == 200:
                                print(f"风扇{fan_id}转速设置成功")
                            
                            time.sleep(0.5)
                        break
                    except Exception as e:
                        print(f"设置风扇转速失败: {e}")
            
            return True
            
        except Exception as e:
            print(f"控制风扇失败: {e}")
            return False
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()

def main():
    print("感谢使用IPMI风扇控制脚本 - 智能分析版")
    print("=" * 60)
    
    # 创建BMC客户端
    client = BMCClient(dic['ip'], dic['username'], dic['password'])
    
    try:
        # 尝试登录
        if client.analyze_and_login():
            print("登录成功！")
            
            # 控制风扇
            if client.control_fans():
                print("风扇控制完成！")
            else:
                print("风扇控制失败")
        else:
            print("登录失败")
            print("\n建议：")
            print("1. 检查用户名和密码是否正确")
            print("2. 确认BMC IP地址是否正确")
            print("3. 使用浏览器手动登录确认系统状态")
            print("4. 尝试使用Selenium自动化脚本")
            
    except Exception as e:
        print(f"程序运行出错: {e}")
    
    finally:
        client.close()

if __name__ == "__main__":
    main()
