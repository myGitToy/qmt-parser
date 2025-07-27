#!/usr/bin/python
# -*- coding: UTF-8 -*-
import http.client
import ssl
import re
import socket
import time
import gzip
import io

dic = {
    'username': 'admin',
    'password': 'admin',
    'ip': '192.168.1.170',
    'speed': '10',  # 需要调整的转速
    'maxConnectivityTest':100, # 超时重连的最大次数
    'fans':["0", "1", "2", "3", "4", "5", "6", "7"] # 需要调整转速的风扇端口 一共8个端口 0~7 （一般默认插的是 0，2，4，6）
}

print("感谢使用修改风扇速度脚本")


def is_port_open(ip_address, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((ip_address, port))
    if result == 0:
        print('bmc控制台端口测试通过   ', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
        return True
    else:
        print('bmc控制台连接超时，端口测试失败    ', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
        return False


index = 0


def loop_func(second):
    global index
    while not is_port_open(dic.get('ip'), 80):
        if index+1 >= dic.get('maxConnectivityTest'):
            return False
        index = index + 1
        time.sleep(second)
    return True


if not loop_func(5):
    print("重连超出最大次数" + str(dic.get('maxConnectivityTest')) + "次。\n请检查网线是否接入管理端口")
    exit()

print(f'用户名: {dic.get("username")}')
print(f'密码: {dic.get("password")}')
print(f'ip: {dic.get("ip")}')
print(f'待调整速度: {dic.get("speed")} %')

print("开始登录bmc------>")
print('——————————————————————————————————————————————————————————————')

# 执行登录请求
try:
    # 检查是否需要HTTPS
    print("检测连接类型...")
    
    # 首先尝试HTTP
    try:
        conn = http.client.HTTPConnection(dic.get("ip"), timeout=10)
        conn.request("GET", "/", "", {})
        response = conn.getresponse()
        
        # 如果返回301/302并且Location包含https，则使用HTTPS
        if response.status in [301, 302]:
            location = response.getheader('Location')
            if location and 'https' in location:
                print("检测到需要HTTPS连接")
                conn.close()
                
                # 创建SSL上下文，忽略证书验证
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                conn = http.client.HTTPSConnection(dic.get("ip"), 443, context=context, timeout=10)
                use_https = True
                protocol = "https"
            else:
                use_https = False
                protocol = "http"
        else:
            use_https = False
            protocol = "http"
            
    except Exception as e:
        print(f"HTTP连接失败，尝试HTTPS: {e}")
        # 创建SSL上下文，忽略证书验证
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        conn = http.client.HTTPSConnection(dic.get("ip"), 443, context=context, timeout=10)
        use_https = True
        protocol = "https"
    
    print(f"使用 {protocol.upper()} 连接")
    
    payload = "WEBVAR_USERNAME=" + dic.get("username") + "&WEBVAR_PASSWORD=" + dic.get("password")
    print(f"登录请求payload: {payload}")
    
    headers = {
        'Accept': "application/json, text/plain, */*",
        'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        'Cache-Control': "no-cache",
        'Connection': "keep-alive",
        'Content-Type': "application/x-www-form-urlencoded",  # 修改为表单格式
        'Origin': f"{protocol}://{dic.get('ip')}",  # 使用检测到的协议
        'Pragma': "no-cache",
        'Referer': f"{protocol}://{dic.get('ip')}/index.html",  # 使用检测到的协议
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
        'Cookie': f"BMC_IP_ADDR={dic.get('ip')}; test=1",  # 使用配置的IP
    }
    
    # 移除压缩头，避免解码问题
    if 'Accept-Encoding' in headers:
        del headers['Accept-Encoding']
    
    def decode_response(response_data):
        """解码响应数据，处理可能的压缩"""
        try:
            # 首先尝试直接解码
            return response_data.decode("utf-8")
        except UnicodeDecodeError:
            try:
                # 尝试gzip解压
                return gzip.decompress(response_data).decode("utf-8")
            except:
                try:
                    # 尝试其他编码
                    return response_data.decode("latin-1")
                except:
                    return str(response_data)
    
    conn.request("POST", "/rpc/WEBSES/create.asp", payload, headers)
    
    response = conn.getresponse()
    response_data = response.read()
    tokenStr = decode_response(response_data)
    
    # 输出调试信息
    print(f"登录请求状态码: {response.status}")
    print(f"响应头: {dict(response.getheaders())}")
    print(f"登录响应内容: {repr(tokenStr)}")
    print('——————————————————————————————————————————————————————————————')
    
    # 如果是重定向，尝试处理
    if response.status == 301 or response.status == 302:
        location = response.getheader('Location')
        print(f"检测到重定向到: {location}")
        
        # 尝试访问重定向的URL
        if location:
            import urllib.parse
            parsed_url = urllib.parse.urlparse(location)
            redirect_path = parsed_url.path
            print(f"尝试访问重定向路径: {redirect_path}")
            
            conn.request("POST", redirect_path, payload, headers)
            response = conn.getresponse()
            response_data = response.read()
            tokenStr = decode_response(response_data)
            print(f"重定向后状态码: {response.status}")
            print(f"重定向后响应: {repr(tokenStr)}")
    
    # 如果响应为空，尝试GET请求获取登录页面
    if not tokenStr.strip():
        print("响应为空，尝试先获取登录页面...")
        conn.request("GET", "/index.html", "", {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        })
        login_response = conn.getresponse()
        login_data = login_response.read()
        login_page = decode_response(login_data)
        print(f"登录页面获取状态: {login_response.status}")
        
        # 再次尝试登录
        conn.request("POST", "/rpc/WEBSES/create.asp", payload, headers)
        response = conn.getresponse()
        response_data = response.read()
        tokenStr = decode_response(response_data)
        print(f"重试登录状态码: {response.status}")
        print(f"重试登录响应: {repr(tokenStr)}")
    
    # 尝试多种可能的SESSION_COOKIE格式
    patterns = [
        r"'SESSION_COOKIE' : '([^']*)'",
        r'"SESSION_COOKIE" : "([^"]*)"',
        r"SESSION_COOKIE['\"]?\s*:\s*['\"]([^'\"]*)['\"]",
        r"SessionCookie['\"]?\s*:\s*['\"]([^'\"]*)['\"]",
        r"session_cookie['\"]?\s*:\s*['\"]([^'\"]*)['\"]",
        r"session['\"]?\s*:\s*['\"]([^'\"]*)['\"]",
        r"token['\"]?\s*:\s*['\"]([^'\"]*)['\"]"
    ]
    
    session_cookie = None
    for pattern in patterns:
        match = re.search(pattern, tokenStr, re.IGNORECASE)
        if match:
            session_cookie = match.group(1)
            print(f"找到Session Cookie (使用模式: {pattern}): {session_cookie}")
            break
    
    if not session_cookie:
        print("未找到SESSION_COOKIE，可能的原因：")
        print("1. 用户名或密码错误")
        print("2. BMC IP地址不正确")
        print("3. BMC服务未启动或版本不兼容")
        print("4. 请求头格式不正确")
        print("5. 需要先访问登录页面获取CSRF token")
        print(f"\n完整响应内容: {repr(tokenStr)}")
        
        # 尝试其他可能的登录端点
        alternative_endpoints = [
            "/rpc/WEBSES/create.asp",
            "/rpc/webses/create.asp",
            "/login.asp",
            "/rpc/login.asp",
            "/api/login",
            "/cgi-bin/login.cgi"
        ]
        
        for endpoint in alternative_endpoints:
            try:
                print(f"尝试登录端点: {endpoint}")
                conn.request("POST", endpoint, payload, headers)
                alt_response = conn.getresponse()
                alt_data = alt_response.read()
                alt_tokenStr = decode_response(alt_data)
                print(f"端点 {endpoint} 状态码: {alt_response.status}")
                
                if alt_response.status == 200 and alt_tokenStr.strip():
                    print(f"端点 {endpoint} 响应内容: {alt_tokenStr[:500]}...")
                    
                    # 检查Set-Cookie头
                    for header_name, header_value in alt_response.getheaders():
                        if header_name.lower() == 'set-cookie':
                            print(f"端点 {endpoint} Set-Cookie: {header_value}")
                            # 尝试解析cookie
                            if 'session' in header_value.lower():
                                cookie_match = re.search(r'([^=]+)=([^;]+)', header_value)
                                if cookie_match:
                                    session_cookie = cookie_match.group(2)
                                    print(f"从Set-Cookie中提取到session: {session_cookie}")
                                    break
                    
                    if session_cookie:
                        break
                    
                    # 如果还没找到，尝试查找响应内容中的session信息
                    for pattern in patterns:
                        match = re.search(pattern, alt_tokenStr, re.IGNORECASE)
                        if match:
                            session_cookie = match.group(1)
                            print(f"在端点 {endpoint} 找到Session Cookie: {session_cookie}")
                            break
                    if session_cookie:
                        break
            except Exception as e:
                print(f"尝试端点 {endpoint} 失败: {e}")
                continue
        
        if not session_cookie:
            # 尝试新的认证方式
            print("尝试其他认证方式...")
            
            # 方式1：尝试JSON格式登录
            try:
                print("尝试JSON格式登录...")
                import json
                json_payload = json.dumps({
                    "username": dic.get("username"),
                    "password": dic.get("password")
                })
                
                json_headers = headers.copy()
                json_headers['Content-Type'] = 'application/json'
                
                conn.request("POST", "/api/session", json_payload, json_headers)
                json_response = conn.getresponse()
                json_data = json_response.read()
                json_content = decode_response(json_data)
                
                print(f"JSON登录状态码: {json_response.status}")
                print(f"JSON登录响应: {json_content}")
                
                # 检查JSON响应中的token
                try:
                    json_obj = json.loads(json_content)
                    if 'token' in json_obj:
                        session_cookie = json_obj['token']
                        print(f"从JSON响应中找到token: {session_cookie}")
                    elif 'session' in json_obj:
                        session_cookie = json_obj['session']
                        print(f"从JSON响应中找到session: {session_cookie}")
                except:
                    pass
                    
            except Exception as e:
                print(f"JSON登录失败: {e}")
            
            # 方式2：尝试直接从Cookie头获取
            if not session_cookie:
                print("尝试从初始响应的Cookie头获取...")
                try:
                    conn.request("GET", "/", "", headers)
                    cookie_response = conn.getresponse()
                    
                    for header_name, header_value in cookie_response.getheaders():
                        if header_name.lower() == 'set-cookie':
                            print(f"初始Cookie: {header_value}")
                            # 查找任何可能的session cookie
                            cookie_patterns = [
                                r'session[^=]*=([^;]+)',
                                r'JSESSIONID=([^;]+)',
                                r'PHPSESSID=([^;]+)',
                                r'ASP\.NET_SessionId=([^;]+)',
                                r'connect\.sid=([^;]+)'
                            ]
                            
                            for cookie_pattern in cookie_patterns:
                                cookie_match = re.search(cookie_pattern, header_value, re.IGNORECASE)
                                if cookie_match:
                                    session_cookie = cookie_match.group(1)
                                    print(f"从初始Cookie中找到session: {session_cookie}")
                                    break
                            if session_cookie:
                                break
                                
                except Exception as e:
                    print(f"获取初始Cookie失败: {e}")
            
            # 方式3：尝试模拟完整的浏览器登录流程
            if not session_cookie:
                print("尝试模拟完整登录流程...")
                try:
                    # 先获取登录页面
                    conn.request("GET", "/index.html", "", {
                        'User-Agent': headers['User-Agent'],
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                    })
                    page_response = conn.getresponse()
                    page_content = decode_response(page_response.read())
                    
                    # 查找CSRF token或其他隐藏字段
                    csrf_patterns = [
                        r'name=["\']?_token["\']?\s+value=["\']([^"\']+)["\']',
                        r'name=["\']?csrf[^"\']*["\']?\s+value=["\']([^"\']+)["\']',
                        r'_token["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                        r'csrf[^"\']*["\']?\s*[:=]\s*["\']([^"\']+)["\']'
                    ]
                    
                    csrf_token = None
                    for csrf_pattern in csrf_patterns:
                        csrf_match = re.search(csrf_pattern, page_content, re.IGNORECASE)
                        if csrf_match:
                            csrf_token = csrf_match.group(1)
                            print(f"找到CSRF token: {csrf_token}")
                            break
                    
                    # 使用CSRF token重新登录
                    if csrf_token:
                        csrf_payload = payload + f"&_token={csrf_token}"
                        conn.request("POST", "/rpc/WEBSES/create.asp", csrf_payload, headers)
                        csrf_response = conn.getresponse()
                        csrf_data = csrf_response.read()
                        csrf_content = decode_response(csrf_data)
                        
                        print(f"CSRF登录状态码: {csrf_response.status}")
                        print(f"CSRF登录响应: {csrf_content[:200]}...")
                        
                        # 再次尝试查找session
                        for pattern in patterns:
                            match = re.search(pattern, csrf_content, re.IGNORECASE)
                            if match:
                                session_cookie = match.group(1)
                                print(f"CSRF登录找到Session Cookie: {session_cookie}")
                                break
                
                except Exception as e:
                    print(f"模拟登录流程失败: {e}")
            
            raise ValueError("SESSION_COOKIE not found in the response")
    
except Exception as e:
    print(f"登录过程中发生错误: {str(e)}")
    conn.close()
    exit()

# 输出截取的信息
print('登录成功')
print(f'获取到Session Cookie: {session_cookie}')
print('——————————————————————————————————————————————————————————————')
print('开始修改风扇为手动')

payload1 = "MODE=1"

headers1 = {
    'Accept': "application/json, text/plain, */*",
    'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    'Cache-Control': "no-cache",
    'Connection': "keep-alive",
    'Content-Type': "application/x-www-form-urlencoded",
    'Origin': f"http://{dic.get('ip')}",
    'Pragma': "no-cache",
    'Referer': f"http://{dic.get('ip')}/main.html",
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    'Cookie': f"BMC_IP_ADDR={dic.get('ip')}; test=1; SessionCookie={session_cookie}; Username=admin; PNO=4; gMultiLAN=true; settings={{eth:[0,1],ethstr:['eth0','eth1'],lan:[8,1],enable:[1,1]}}",
}

conn.request("POST", "/rpc/setfanmode.asp", payload1, headers1)
conn.getresponse().read().decode("utf-8")
print('已修改风扇为手动')
print('——————————————————————————————————————————————————————————————')
print('开始调整风扇风速')
headers2 = {
    'Accept': "application/json, text/plain, */*",
    'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    'Cache-Control': "no-cache",
    'Connection': "keep-alive",
    'Content-Type': "application/x-www-form-urlencoded",
    'Origin': f"http://{dic.get('ip')}",
    'Pragma': "no-cache",
    'Referer': f"http://{dic.get('ip')}/main.html",
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    'Cookie': f"test=1; SessionCookie={session_cookie}; BMC_IP_ADDR={dic.get('ip')}; Username=admin; PNO=4; gMultiLAN=true; settings={{eth:[0,1],ethstr:['eth0','eth1'],lan:[8,1],enable:[1,1]}}",
}
for x in dic.get('fans'):
    print("调整风扇" + x)
    payload2 = "ID=" + x + "&PERCENT=" + dic.get("speed")
    conn.request("POST", "/rpc/setfanspeed.asp", payload2, headers2)
    conn.getresponse().read().decode("utf-8")
    print("调整风扇" + x + "完成")
print('——————————————————————————————————————————————————————————————')
print('关闭连接')
conn.close()
print('退出脚本')
exit()

