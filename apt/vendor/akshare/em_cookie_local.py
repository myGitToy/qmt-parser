import os
import json
import sqlite3
import shutil
import tempfile
import time
from pathlib import Path
import psutil
import subprocess
import socket
import requests
import urllib.parse
import websocket
import threading
import uuid

def is_chrome_running():
    """检查Chrome浏览器是否正在运行"""
    for proc in psutil.process_iter(['name']):
        try:
            if 'chrome' in proc.info['name'].lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def get_chrome_user_data_path():
    """获取Chrome用户数据路径"""
    local_app_data = os.environ.get('LOCALAPPDATA')
    chrome_paths = [
        os.path.join(local_app_data, 'Google', 'Chrome', 'User Data'),
        os.path.join(local_app_data, 'Google', 'Chrome Beta', 'User Data'),
        os.path.join(local_app_data, 'Google', 'Chrome SxS', 'User Data'),
        os.path.join(local_app_data, 'Google', 'Chrome Dev', 'User Data')
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            return path
    
    raise FileNotFoundError("无法找到Chrome用户数据目录")

def get_eastmoney_cookie_from_chrome(max_retries=3, retry_interval=2):
    """从Chrome浏览器获取东方财富网站的Cookie，带重试机制"""
    
    # 检查Chrome是否在运行
    if is_chrome_running():
        print("警告: Chrome浏览器正在运行，可能无法访问Cookie文件。")
        print("建议: 关闭Chrome浏览器后重试，或尝试使用CDP方法获取。")
    
    # 获取Chrome用户数据路径
    try:
        user_data_dir = get_chrome_user_data_path()
        cookie_path = os.path.join(user_data_dir, 'Default', 'Network', 'Cookies')
        
        # 如果Default目录不存在，尝试Profile 1等
        if not os.path.exists(cookie_path):
            profiles = [d for d in os.listdir(user_data_dir) if d.startswith('Profile')]
            if profiles:
                cookie_path = os.path.join(user_data_dir, profiles[0], 'Network', 'Cookies')
    except FileNotFoundError as e:
        print(f"错误: {e}")
        return None
    
    # 确保路径中没有重复的反斜杠
    cookie_path = os.path.normpath(cookie_path)
    
    # 使用临时目录
    temp_dir = tempfile.gettempdir()
    temp_cookie_path = os.path.join(temp_dir, f'chrome_cookies_copy_{int(time.time())}.db')
    
    for attempt in range(max_retries):
        try:
            # 检查源文件是否存在
            if not os.path.exists(cookie_path):
                print(f"Cookie文件不存在: {cookie_path}")
                return None
            
            # 复制Cookie文件
            shutil.copy2(cookie_path, temp_cookie_path)
            
            # 连接到复制的数据库
            conn = sqlite3.connect(temp_cookie_path)
            cursor = conn.cursor()
            
            # 查询东方财富网站的Cookie
            domains = ['eastmoney.com', '.eastmoney.com', 'quote.eastmoney.com', 'fund.eastmoney.com']
            
            cookies = {}
            
            try:
                # 尝试新版Chrome的加密Cookie表结构
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cookies'")
                if cursor.fetchone():
                    for domain in domains:
                        cursor.execute(
                            "SELECT name, value FROM cookies WHERE host_key LIKE ? OR host_key LIKE ?", 
                            (f"%{domain}%", f"%.{domain}%")
                        )
                        results = cursor.fetchall()
                        for name, value in results:
                            cookies[name] = value
            except sqlite3.OperationalError:
                print("警告: 无法读取新版Chrome Cookie表")
            
            # 构建Cookie字符串
            if cookies:
                cookie_str = "; ".join([f"{name}={value}" for name, value in cookies.items()])
                return cookie_str
            else:
                print("未找到东方财富网站的Cookie")
                return None
            
        except PermissionError as e:
            if attempt < max_retries - 1:
                print(f"权限错误: {e}. 尝试重试 ({attempt + 1}/{max_retries})...")
                time.sleep(retry_interval)
            else:
                print("多次尝试后仍无法访问Cookie文件，尝试使用CDP方法获取...")
                # 如果Chrome正在运行，尝试使用CDP方法
                if is_chrome_running():
                    try:
                        return get_eastmoney_cookie_from_cdp()
                    except Exception as cdp_e:
                        print(f"CDP方法获取失败: {cdp_e}")
                return None
        except Exception as e:
            print(f"读取Chrome Cookie时出错: {e}")
            return None
        finally:
            # 关闭连接并删除临时文件
            if 'conn' in locals() and conn:
                conn.close()
            if os.path.exists(temp_cookie_path):
                try:
                    os.remove(temp_cookie_path)
                except PermissionError:
                    pass  # 忽略临时文件删除失败

def get_cookie_from_env():
    """从环境变量获取Cookie的方法已被禁用"""
    print("已禁用从环境变量获取Cookie的功能")
    return None

def start_chrome_with_debugging(timeout=10):
    """启动一个带有远程调试端口的Chrome实例"""
    try:
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
        
        # 查找可用的端口
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 0))
        debug_port = s.getsockname()[1]
        s.close()
        
        # 构建Chrome命令
        cmd = [
            chrome_exe,
            f"--remote-debugging-port={debug_port}",
            "--remote-allow-origins=*",  # 允许所有源的WebSocket连接
            "--user-data-dir=" + os.path.join(tempfile.gettempdir(), f"chrome_debug_profile_{int(time.time())}"),
            "--no-first-run",
            "--no-default-browser-check",
            "https://www.eastmoney.com"
        ]
        
        print(f"启动带调试端口的Chrome: {debug_port}")
        
        # 使用subprocess启动Chrome
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待Chrome启动并加载页面
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                print("等待Chrome启动超时")
                process.terminate()
                return None
            
            try:
                response = requests.get(f"http://localhost:{debug_port}/json/version", timeout=1)
                if response.status_code == 200:
                    print("Chrome已启动，调试端口可用")
                    return debug_port
            except requests.exceptions.RequestException:
                time.sleep(0.5)
                continue
            
            time.sleep(0.5)
    
    except Exception as e:
        print(f"启动Chrome时出错: {e}")
        return None

def get_eastmoney_cookie_from_file():
    """从本地文件读取Cookie"""
    try:
        # 检查是否存在Cookie文件
        cookie_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eastmoney_cookie.txt")
        
        if os.path.exists(cookie_file):
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookie_str = f.read().strip()
                
            if cookie_str:
                print(f"从文件成功读取到Cookie，长度: {len(cookie_str)}字符")
                return cookie_str
            else:
                print("Cookie文件为空")
        else:
            print(f"Cookie文件不存在: {cookie_file}")
        
        return None
    except Exception as e:
        print(f"读取Cookie文件时出错: {e}")
        return None

def get_eastmoney_cookie_from_cdp():
    """通过Chrome DevTools Protocol从运行中的Chrome获取Cookie"""
    try:
        # 尝试先从文件中读取
        cookie_from_file = get_eastmoney_cookie_from_file()
        if cookie_from_file:
            return cookie_from_file
            
        # 获取调试端口
        debug_port = None
        chrome_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'chrome' in proc.info['name'].lower():
                    chrome_processes.append(proc)
                    if proc.info['cmdline'] and any('--remote-debugging-port=' in arg for arg in proc.info['cmdline']):
                        for arg in proc.info['cmdline']:
                            if arg.startswith('--remote-debugging-port='):
                                debug_port = int(arg.split('=')[1])
                                break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # 如果没有找到调试端口，尝试启动一个新的Chrome实例
        if not debug_port:
            print("没有找到已启用调试端口的Chrome实例，尝试启动一个新实例...")
            debug_port = start_chrome_with_debugging()
            
            if not debug_port:
                print("无法启动带调试功能的Chrome，请手动启动Chrome并指定调试端口")
                print("命令示例: chrome.exe --remote-debugging-port=9222 https://www.eastmoney.com")
                return None
        
        # 连接到Chrome DevTools Protocol
        response = requests.get(f"http://localhost:{debug_port}/json/list")
        if response.status_code != 200:
            print(f"无法连接到Chrome DevTools Protocol: {response.status_code}")
            return None
        
        targets = response.json()
        
        # 找到包含eastmoney.com的标签页
        eastmoney_targets = [t for t in targets if 'eastmoney.com' in t.get('url', '')]
        if not eastmoney_targets:
            print("没有找到打开的东方财富网站标签页，尝试打开...")
            
            # 尝试使用已存在的标签页
            for t in targets:
                if t.get('type') == 'page' and 'webSocketDebuggerUrl' in t:
                    target = t
                    
                    # 向该页面发送导航指令
                    try:
                        ws_url = target['webSocketDebuggerUrl']
                        ws = websocket.create_connection(ws_url)
                        msg_id = str(uuid.uuid4().int)
                        
                        # 导航到东方财富网站
                        ws.send(json.dumps({
                            "id": msg_id,
                            "method": "Page.navigate",
                            "params": {
                                "url": "https://www.eastmoney.com"
                            }
                        }))
                        
                        # 等待导航完成
                        ws.recv()
                        ws.close()
                        
                        print("已打开东方财富网站，等待3秒加载...")
                        time.sleep(3)
                        
                        # 重新获取标签页列表
                        response = requests.get(f"http://localhost:{debug_port}/json/list")
                        if response.status_code == 200:
                            targets = response.json()
                            # 再次查找东方财富标签页
                            eastmoney_targets = [t for t in targets if 'eastmoney.com' in t.get('url', '')]
                            if eastmoney_targets:
                                target = eastmoney_targets[0]
                                break
                    except Exception as e:
                        print(f"导航到东方财富网站出错: {e}")
                        continue
                        
            # 如果仍然没有找到
            if not eastmoney_targets:
                print("无法打开东方财富网站")
                return None
        else:
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
            print(f"通过Chrome DevTools Protocol成功获取到 {len(eastmoney_cookies)} 个Cookie")
            
            # 保存Cookie到文件以便后续使用
            try:
                cookie_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eastmoney_cookie.txt")
                with open(cookie_file, 'w', encoding='utf-8') as f:
                    f.write(cookie_str)
                print(f"已将Cookie保存到文件: {cookie_file}")
            except Exception as e:
                print(f"保存Cookie到文件时出错: {e}")
                
            return cookie_str
        else:
            print("没有找到东方财富网站的Cookie")
            return None
    
    except Exception as e:
        print(f"通过Chrome DevTools Protocol获取Cookie失败: {e}")
        return None

def get_eastmoney_cookie():
    """获取东方财富Cookie的主函数，智能选择获取方式"""
    cookie = None
    
    # 检查Chrome是否在运行
    chrome_running = is_chrome_running()
    
    # 如果Chrome正在运行，优先尝试CDP方法
    if chrome_running:
        try:
            print("检测到Chrome正在运行，尝试通过CDP方法获取Cookie...")
            cookie = get_eastmoney_cookie_from_cdp()
            if cookie:
                print("CDP方法获取Cookie成功！")
                return cookie
            else:
                print("CDP方法未找到Cookie，尝试文件读取方法...")
        except ImportError:
            print("缺少websocket-client库，无法使用CDP方法")
            print("可通过运行 'pip install websocket-client' 安装")
        except Exception as e:
            print(f"CDP方法发生错误: {e}")
    
    # 尝试从Chrome文件获取
    cookie = get_eastmoney_cookie_from_chrome()
    
    # 如果文件方法失败且之前没尝试过CDP，则尝试CDP
    if cookie is None and not chrome_running:
        try:
            print("文件读取失败，尝试通过CDP方法获取Cookie...")
            cookie = get_eastmoney_cookie_from_cdp()
            if cookie:
                print("CDP方法获取Cookie成功！")
        except Exception:
            pass
    
    return cookie

if __name__ == "__main__":
    print("正在检查所需模块...")
    missing_modules = []
    for module_name in ["websocket-client", "psutil"]:
        try:
            if module_name == "websocket-client":
                import websocket
            elif module_name == "psutil":
                import psutil
        except ImportError:
            missing_modules.append(module_name)
    
    if missing_modules:
        print(f"警告: 缺少以下Python模块: {', '.join(missing_modules)}")
        print("推荐使用以下命令安装:")
        for module in missing_modules:
            print(f"    pip install {module}")
        print("安装后重试可获得更好的结果\n")
    
    print("正在从浏览器缓存获取东方财富Cookie...")
    cookie_str = get_eastmoney_cookie()
    if cookie_str:
        print("\n获取到的Cookie字符串:")
        print(cookie_str[:100] + "..." if len(cookie_str) > 100 else cookie_str)
        print(f"\nCookie长度: {len(cookie_str)} 字符")
    else:
        print("未能获取到Cookie。请确保已登录东方财富网站且浏览器中有有效的Cookie缓存。")