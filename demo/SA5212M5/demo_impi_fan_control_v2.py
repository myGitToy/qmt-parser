#!/usr/bin/python
# -*- coding: UTF-8 -*-
import http.client
import ssl
import re
import socket
import time
import json
import hashlib
import base64

dic = {
    'username': 'admin',
    'password': 'admin',
    'ip': '192.168.1.170',
    'speed': '10',  # 需要调整的转速
    'maxConnectivityTest': 100,  # 超时重连的最大次数
    'fans': ["0", "1", "2", "3", "4", "5", "6", "7"]  # 需要调整转速的风扇端口
}

print("感谢使用修改风扇速度脚本 (v2)")

def is_port_open(ip_address, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((ip_address, port))
    if result == 0:
        print('bmc控制台端口测试通过   ', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
        return True
    else:
        print('bmc控制台连接超时，端口测试失败    ', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
        return False

def create_connection(ip):
    """创建HTTPS连接"""
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        conn = http.client.HTTPSConnection(ip, 443, context=context, timeout=30)
        return conn, "https"
    except Exception as e:
        print(f"HTTPS连接失败，尝试HTTP: {e}")
        try:
            conn = http.client.HTTPConnection(ip, 80, timeout=30)
            return conn, "http"
        except Exception as e2:
            print(f"HTTP连接也失败: {e2}")
            return None, None

def blowfish_encrypt(data, key):
    """模拟Blowfish加密 (简化版)"""
    # 这里应该实现完整的Blowfish加密，现在先返回Base64编码的数据
    return base64.b64encode(data.encode()).decode()

def try_modern_login(conn, protocol, ip, username, password):
    """尝试现代BMC登录方式"""
    login_methods = [
        {
            'name': 'JSON API Login',
            'url': '/api/login',
            'method': 'POST',
            'headers': {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            'data': json.dumps({
                'username': username,
                'password': password
            })
        },
        {
            'name': 'Session API Login',
            'url': '/api/session',
            'method': 'POST',
            'headers': {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            'data': json.dumps({
                'username': username,
                'password': password
            })
        },
        {
            'name': 'Form Login',
            'url': '/login',
            'method': 'POST',
            'headers': {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            },
            'data': f'username={username}&password={password}'
        },
        {
            'name': 'BMC Login',
            'url': '/rpc/login',
            'method': 'POST',
            'headers': {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            },
            'data': f'username={username}&password={password}'
        }
    ]
    
    for method in login_methods:
        try:
            print(f"尝试 {method['name']} 登录方式...")
            
            conn.request(method['method'], method['url'], method['data'], method['headers'])
            response = conn.getresponse()
            response_data = response.read()
            
            print(f"状态码: {response.status}")
            print(f"响应头: {dict(response.getheaders())}")
            
            try:
                response_text = response_data.decode('utf-8')
                print(f"响应内容: {response_text[:500]}...")
                
                # 检查是否有session token
                if response.status == 200:
                    # 尝试解析JSON
                    try:
                        json_data = json.loads(response_text)
                        if 'token' in json_data:
                            return json_data['token']
                        if 'session' in json_data:
                            return json_data['session']
                        if 'sessionId' in json_data:
                            return json_data['sessionId']
                    except:
                        pass
                    
                    # 查找Set-Cookie头
                    for header_name, header_value in response.getheaders():
                        if header_name.lower() == 'set-cookie':
                            if 'session' in header_value.lower():
                                cookie_parts = header_value.split(';')[0].split('=')
                                if len(cookie_parts) == 2:
                                    return cookie_parts[1]
                
            except UnicodeDecodeError:
                print("响应内容无法解码")
                
        except Exception as e:
            print(f"{method['name']} 失败: {e}")
            continue
    
    return None

def try_ajax_login(conn, protocol, ip, username, password):
    """尝试Ajax登录"""
    try:
        # 首先获取登录页面，可能需要CSRF token
        print("获取登录页面...")
        conn.request("GET", "/", "", {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        page_response = conn.getresponse()
        page_content = page_response.read().decode('utf-8')
        
        # 查找CSRF token
        csrf_patterns = [
            r'csrf[_-]?token["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'_token["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'token["\']?\s*[:=]\s*["\']([^"\']+)["\']'
        ]
        
        csrf_token = None
        for pattern in csrf_patterns:
            match = re.search(pattern, page_content, re.IGNORECASE)
            if match:
                csrf_token = match.group(1)
                print(f"找到CSRF token: {csrf_token}")
                break
        
        # 尝试Ajax登录
        ajax_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': f'{protocol}://{ip}/'
        }
        
        # 构建登录数据
        login_data = f'username={username}&password={password}'
        if csrf_token:
            login_data += f'&_token={csrf_token}'
        
        print("发送Ajax登录请求...")
        conn.request("POST", "/login", login_data, ajax_headers)
        ajax_response = conn.getresponse()
        ajax_content = ajax_response.read().decode('utf-8')
        
        print(f"Ajax登录状态: {ajax_response.status}")
        print(f"Ajax登录响应: {ajax_content}")
        
        # 检查Set-Cookie
        for header_name, header_value in ajax_response.getheaders():
            if header_name.lower() == 'set-cookie':
                print(f"Set-Cookie: {header_value}")
                # 解析session cookie
                if 'session' in header_value.lower():
                    cookie_parts = header_value.split(';')[0].split('=')
                    if len(cookie_parts) == 2:
                        return cookie_parts[1]
        
        return None
        
    except Exception as e:
        print(f"Ajax登录失败: {e}")
        return None

def main():
    # 端口检查
    if not is_port_open(dic.get('ip'), 443) and not is_port_open(dic.get('ip'), 80):
        print("BMC端口连接失败")
        return
    
    print(f'用户名: {dic.get("username")}')
    print(f'密码: {dic.get("password")}')
    print(f'IP: {dic.get("ip")}')
    print(f'待调整速度: {dic.get("speed")} %')
    print("开始登录BMC...")
    print('—' * 60)
    
    # 创建连接
    conn, protocol = create_connection(dic.get('ip'))
    if not conn:
        print("无法创建连接")
        return
    
    print(f"使用 {protocol.upper()} 连接")
    
    # 尝试不同的登录方式
    session_token = None
    
    # 方式1: 现代API登录
    session_token = try_modern_login(conn, protocol, dic.get('ip'), dic.get('username'), dic.get('password'))
    
    # 方式2: Ajax登录
    if not session_token:
        session_token = try_ajax_login(conn, protocol, dic.get('ip'), dic.get('username'), dic.get('password'))
    
    if not session_token:
        print("所有登录方式均失败")
        print("可能的原因：")
        print("1. 用户名或密码错误")
        print("2. BMC固件版本不支持")
        print("3. 需要特殊的认证方式")
        print("4. IP地址错误")
        conn.close()
        return
    
    print(f"登录成功，Session Token: {session_token}")
    print('—' * 60)
    
    # 后续的风扇控制逻辑...
    print("登录成功，但风扇控制功能需要进一步分析BMC的API接口")
    
    conn.close()

if __name__ == "__main__":
    main()
