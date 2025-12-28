"""
修复Chrome远程调试权限问题并获取东方财富Cookie
"""

import os
import sys
import subprocess
import time
import tempfile
import json
import socket
import requests
import uuid
import websocket
from pathlib import Path

def find_chrome_executable():
    """查找Chrome可执行文件路径"""
    chrome_paths = [
        os.path.join(os.environ.get('PROGRAMFILES', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
        os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'Application', 'chrome.exe')
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            return path
    
    return None

def start_debug_chrome():
    """启动带有远程调试功能的Chrome"""
    chrome_exe = find_chrome_executable()
    if not chrome_exe:
        print("错误: 无法找到Chrome浏览器")
        return None
    
    # 使用固定端口便于后续连接
    debug_port = 9222
    
    # 创建临时用户数据目录
    user_data_dir = os.path.join(tempfile.gettempdir(), f"chrome_debug_{int(time.time())}")
    
    # 构建命令行
    cmd = [
        chrome_exe,
        f"--remote-debugging-port={debug_port}",
        "--remote-allow-origins=*",  # 关键参数，允许任何源连接
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "https://www.eastmoney.com"
    ]
    
    print("\n正在启动Chrome浏览器...")
    print(f"调试端口: {debug_port}")
    print(f"用户数据目录: {user_data_dir}")
    
    # 启动Chrome
    process = subprocess.Popen(cmd)
    
    # 等待调试端口可用
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"http://localhost:{debug_port}/json/version", timeout=1)
            if response.status_code == 200:
                print("Chrome已成功启动且调试端口已开放")
                print("\n请在打开的Chrome窗口中登录东方财富网站")
                print("完成登录后，请按回车键继续...\n")
                input()
                return debug_port
        except:
            pass
        
        time.sleep(1)
        print(f"等待Chrome启动中... {i+1}/{max_retries}")
    
    print("错误: Chrome启动超时或无法开放调试端口")
    return None

def get_cookie_from_chrome(debug_port=9222):
    """通过CDP获取Cookie"""
    try:
        # 连接到Chrome DevTools Protocol
        print("\n正在连接到Chrome调试端口...")
        response = requests.get(f"http://localhost:{debug_port}/json/list")
        if response.status_code != 200:
            print(f"错误: 无法连接到Chrome调试接口，状态码 {response.status_code}")
            return None
        
        # 获取标签页列表
        targets = response.json()
        
        # 查找东方财富网站的标签页
        eastmoney_targets = [t for t in targets if 'eastmoney.com' in t.get('url', '')]
        if not eastmoney_targets:
            print("错误: 未找到打开的东方财富网站标签页")
            return None
        
        target = eastmoney_targets[0]
        print(f"找到东方财富网站标签页: {target['url']}")
        
        # 连接WebSocket
        print("正在通过WebSocket连接获取Cookie...")
        ws_url = target['webSocketDebuggerUrl']
        ws = websocket.create_connection(ws_url)
        
        # 获取所有Cookie
        msg_id = str(uuid.uuid4().int)
        ws.send(json.dumps({
            "id": msg_id,
            "method": "Network.getAllCookies"
        }))
        
        # 接收响应
        result = json.loads(ws.recv())
        ws.close()
        
        # 筛选东方财富相关的Cookie
        all_cookies = result.get('result', {}).get('cookies', [])
        eastmoney_cookies = [c for c in all_cookies 
                             if any(domain in c.get('domain', '') 
                                   for domain in ['eastmoney.com', '.eastmoney.com'])]
        
        if not eastmoney_cookies:
            print("错误: 未找到东方财富网站的Cookie")
            return None
        
        # 构建Cookie字符串
        cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in eastmoney_cookies])
        print(f"成功获取到 {len(eastmoney_cookies)} 个Cookie!")
        
        # 保存Cookie到文件
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cookie_file = os.path.join(script_dir, "eastmoney_cookie.txt")
        
        with open(cookie_file, 'w', encoding='utf-8') as f:
            f.write(cookie_str)
        
        print(f"\nCookie已保存到: {cookie_file}")
        print(f"Cookie字符串长度: {len(cookie_str)} 字符")
        print("Cookie前100个字符:")
        print(cookie_str[:100] + ("..." if len(cookie_str) > 100 else ""))
        
        return cookie_str
        
    except websocket.WebSocketException as e:
        print(f"WebSocket连接错误: {e}")
        print("\n解决方案: 请确保Chrome已启动且带有 '--remote-allow-origins=*' 参数")
        return None
    except Exception as e:
        print(f"获取Cookie过程中出错: {e}")
        return None

if __name__ == "__main__":
    try:
        import websocket
    except ImportError:
        print("错误: 缺少必要的websocket-client库")
        print("请通过以下命令安装: pip install websocket-client")
        sys.exit(1)
    
    print("==== 东方财富Cookie获取工具 ====\n")
    debug_port = start_debug_chrome()
    
    if debug_port:
        cookie = get_cookie_from_chrome(debug_port)
        if cookie:
            print("\n操作成功完成!")
        else:
            print("\n获取Cookie失败!")
    else:
        print("\n无法启动Chrome浏览器，操作取消。")