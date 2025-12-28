"""
使用Chrome DevTools Protocol启动Chrome并获取东方财富网站Cookie
"""
import os
import sys
import time
import subprocess
import json
import tempfile
import requests
import websocket
import uuid
import pathlib

def start_chrome_with_debugging():
    """启动一个带有远程调试端口的Chrome实例"""
    # Chrome可能的路径
    chrome_paths = [
        os.path.join(os.environ.get('PROGRAMFILES', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
        os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'Application', 'chrome.exe')
    ]
    
    # 查找可用的Chrome路径
    chrome_exe = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_exe = path
            break
    
    if not chrome_exe:
        print("无法找到Chrome可执行文件")
        return None
    
    # 调试端口
    debug_port = 9222
    
    # 构建Chrome命令
    cmd = [
        chrome_exe,
        f"--remote-debugging-port={debug_port}",
        "--remote-allow-origins=*",  # 允许所有源的WebSocket连接
        "--user-data-dir=" + os.path.join(tempfile.gettempdir(), f"chrome_debug_profile_{int(time.time())}"),
        "--no-first-run",
        "--no-default-browser-check",
        "https://www.eastmoney.com"]    
    print(f"启动带调试端口的Chrome: {debug_port}")
    print("请在打开的Chrome窗口中登录东方财富网站")
    print("完成登录后，请按Enter键继续...")
    
    # 使用subprocess启动Chrome
    process = subprocess.Popen(cmd)
    
    # 等待用户登录
    input()
    
    return debug_port

def get_eastmoney_cookie(debug_port=9222):
    """获取东方财富网站的Cookie"""
    try:
        # 连接到Chrome DevTools Protocol
        response = requests.get(f"http://localhost:{debug_port}/json/list")
        if response.status_code != 200:
            print(f"无法连接到Chrome DevTools Protocol: {response.status_code}")
            return None
        
        targets = response.json()
        
        # 找到包含eastmoney.com的标签页
        eastmoney_targets = [t for t in targets if 'eastmoney.com' in t.get('url', '')]
        if not eastmoney_targets:
            print("没有找到打开的东方财富网站标签页")
            return None
        
        target = eastmoney_targets[0]
        
        # 连接WebSocket
        ws_url = target['webSocketDebuggerUrl']
        ws = websocket.create_connection(ws_url)
        
        # 获取Cookie
        msg_id = str(uuid.uuid4().int)
        ws.send(json.dumps({
            "id": msg_id,
            "method": "Network.getAllCookies"
        }))
        
        result = json.loads(ws.recv())
        ws.close()
        
        # 筛选东方财富网站的Cookie
        all_cookies = result.get('result', {}).get('cookies', [])
        eastmoney_cookies = [c for c in all_cookies 
                           if any(domain in c.get('domain', '') for domain in ['eastmoney.com', '.eastmoney.com'])]
        
        if eastmoney_cookies:
            # 构建Cookie字符串
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in eastmoney_cookies])
            print(f"成功获取到 {len(eastmoney_cookies)} 个Cookie")
            
            # 保存Cookie到文件
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eastmoney_cookie.txt")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cookie_str)
            print(f"Cookie已保存到: {file_path}")
            
            return cookie_str
        else:
            print("没有找到东方财富网站的Cookie")
            return None
        
    except Exception as e:
        print(f"获取Cookie失败: {e}")
        return None

if __name__ == "__main__":
    print("本程序将启动Chrome浏览器并获取东方财富网站的Cookie")
    debug_port = start_chrome_with_debugging()
    
    if debug_port:
        cookie = get_eastmoney_cookie(debug_port)
        if cookie:
            print("\nCookie字符串前100字符:")
            print(cookie[:100] + "..." if len(cookie) > 100 else cookie)
            print(f"\nCookie长度: {len(cookie)} 字符")
        else:
            print("获取Cookie失败")