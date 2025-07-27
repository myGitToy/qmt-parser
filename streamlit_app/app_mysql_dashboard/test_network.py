#!/usr/bin/env python3
"""
网络连接测试脚本
用于诊断localhost访问问题
"""

import socket
import subprocess
import sys
import time
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

def test_localhost_resolution():
    """测试localhost域名解析"""
    print("1. 测试localhost域名解析...")
    try:
        ip = socket.gethostbyname('localhost')
        print(f"   ✓ localhost -> {ip}")
        return True
    except Exception as e:
        print(f"   ✗ localhost解析失败: {e}")
        return False

def test_port_binding(port):
    """测试端口绑定"""
    print(f"2. 测试端口 {port} 绑定...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('localhost', port))
        sock.listen(1)
        print(f"   ✓ 端口 {port} 绑定成功")
        sock.close()
        return True
    except Exception as e:
        print(f"   ✗ 端口 {port} 绑定失败: {e}")
        return False

def test_web_server(port):
    """启动临时Web服务器测试"""
    print(f"3. 启动临时Web服务器测试...")
    
    class TestHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>网络测试成功</title></head>
            <body>
                <h1>🎉 网络连接测试成功!</h1>
                <p>端口 {port} 工作正常</p>
                <p>时间: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>现在可以启动MySQL监控应用了</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
    
    try:
        server = HTTPServer(('localhost', port), TestHandler)
        print(f"   ✓ Web服务器启动成功: http://localhost:{port}")
        
        # 在新线程中启动服务器
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        # 尝试打开浏览器
        print("   正在打开浏览器...")
        time.sleep(1)
        webbrowser.open(f'http://localhost:{port}')
        
        print("   按任意键停止测试服务器...")
        input()
        
        server.shutdown()
        return True
        
    except Exception as e:
        print(f"   ✗ Web服务器启动失败: {e}")
        return False

def check_firewall():
    """检查防火墙设置"""
    print("4. 检查防火墙设置...")
    
    if sys.platform.startswith('win'):
        try:
            # Windows防火墙检查
            result = subprocess.run([
                'netsh', 'advfirewall', 'firewall', 'show', 'rule', 
                'name=all', 'dir=in', 'protocol=tcp', 'localport=8501'
            ], capture_output=True, text=True, timeout=10)
            
            if 'Allow' in result.stdout:
                print("   ✓ 防火墙允许端口8501")
            else:
                print("   ⚠ 防火墙可能阻止端口8501")
                print("   建议: 添加防火墙例外或暂时关闭防火墙测试")
        except:
            print("   ⚠ 无法检查防火墙设置")
    else:
        print("   ⚠ 非Windows系统，请手动检查防火墙设置")

def check_streamlit_installation():
    """检查Streamlit安装"""
    print("5. 检查Streamlit安装...")
    try:
        import streamlit
        print(f"   ✓ Streamlit已安装，版本: {streamlit.__version__}")
        return True
    except ImportError:
        print("   ✗ Streamlit未安装")
        install = input("   是否安装Streamlit? (y/n): ").lower()
        if install == 'y':
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'streamlit'])
            return True
        return False

def main():
    print("=" * 60)
    print("localhost访问问题诊断工具")
    print("=" * 60)
    
    # 执行各项测试
    tests = [
        test_localhost_resolution(),
        test_port_binding(8501),
        check_streamlit_installation()
    ]
    
    check_firewall()
    
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    
    if all(tests):
        print("✓ 所有基础测试通过")
        
        # 启动Web服务器测试
        if test_web_server(8501):
            print("\n🎉 网络连接完全正常!")
            print("现在可以启动MySQL监控应用了")
        else:
            print("\n⚠ Web服务器测试失败，可能存在端口冲突")
    else:
        print("✗ 存在问题，请根据上述提示解决")
        
        print("\n故障排除建议:")
        print("1. 重启计算机")
        print("2. 检查杀毒软件/防火墙设置")
        print("3. 尝试使用其他端口 (如8502, 8503)")
        print("4. 以管理员身份运行")
        print("5. 检查网络代理设置")

if __name__ == "__main__":
    main()
