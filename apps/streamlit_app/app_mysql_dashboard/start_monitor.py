#!/usr/bin/env python3
"""
MySQL数据库监控WebUI启动脚本
解决ScriptRunContext警告问题
"""

import os
import sys
import subprocess
import platform
import socket
import time

def diagnose_network():
    """诊断网络连接问题"""
    print("\n正在进行网络诊断...")
    
    # 检查localhost解析
    try:
        ip = socket.gethostbyname('localhost')
        print(f"✓ localhost解析正常: {ip}")
    except:
        print("✗ localhost解析失败")
        return False
    
    # 检查端口可用性
    def test_port(port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.bind(('localhost', port))
            sock.close()
            return True
        except:
            return False
    
    # 测试常用端口
    test_ports = [8501, 8502, 8503, 8080, 3000]
    available_ports = []
    
    for port in test_ports:
        if test_port(port):
            available_ports.append(port)
            print(f"✓ 端口 {port} 可用")
        else:
            print(f"✗ 端口 {port} 被占用")
    
    if not available_ports:
        print("✗ 所有测试端口都被占用")
        return False
    
    print(f"✓ 建议使用端口: {available_ports[0]}")
    return available_ports[0]

def check_dependencies():
    """检查依赖包是否安装"""
    required_packages = [
        ('streamlit', 'streamlit'),
        ('pandas', 'pandas'), 
        ('pymysql', 'pymysql'),
        ('plotly', 'plotly'),
        ('python-dotenv', 'dotenv')  # 包名和导入名不同
    ]
    
    missing_packages = []
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"   ✓ {package_name} 已安装")
        except ImportError:
            missing_packages.append(package_name)
            print(f"   ✗ {package_name} 未安装")
    
    if missing_packages:
        print(f"\n缺少以下依赖包: {', '.join(missing_packages)}")
        
        install = input("\n是否自动安装？(y/n): ").lower()
        if install == 'y':
            for package in missing_packages:
                print(f"正在安装 {package}...")
                result = subprocess.run([sys.executable, '-m', 'pip', 'install', package])
                if result.returncode == 0:
                    print(f"   ✓ {package} 安装成功")
                else:
                    print(f"   ✗ {package} 安装失败")
        else:
            print("请手动安装缺少的依赖包")
            return False
    else:
        print("✓ 所有依赖包都已安装")
    
    return True

def start_streamlit():
    """启动Streamlit应用"""
    # 设置环境变量以减少警告
    os.environ['STREAMLIT_LOGGER_LEVEL'] = 'error'
    os.environ['STREAMLIT_CLIENT_SHOW_ERROR_DETAILS'] = 'false'
    
    # 检查端口是否被占用
    import socket
    def check_port(host, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    port = 8501
    # 如果8501被占用，尝试其他端口
    while check_port('localhost', port) and port < 8510:
        port += 1
    
    # 构建启动命令
    # 获取mysql_monitor.py的完整路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mysql_monitor_path = os.path.join(script_dir, "mysql_monitor.py")
    
    if not os.path.exists(mysql_monitor_path):
        print(f"错误: 找不到mysql_monitor.py文件: {mysql_monitor_path}")
        print("请确保mysql_monitor.py文件与此脚本在同一目录下")
        return
    
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', mysql_monitor_path,
        '--server.port', str(port),
        '--server.address', '0.0.0.0',  # 允许外部访问
        '--server.headless', 'false',
        '--browser.gatherUsageStats', 'false',
        '--logger.level', 'error'
    ]
    
    print("正在启动MySQL数据库监控WebUI...")
    print(f"本地访问地址: http://localhost:{port}")
    print(f"网络访问地址: http://127.0.0.1:{port}")
    
    # 获取本机IP地址
    try:
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"局域网访问地址: http://{local_ip}:{port}")
    except:
        pass
    
    print("按 Ctrl+C 停止服务\n")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n服务已停止")
    except subprocess.CalledProcessError as e:
        print(f"启动失败: {e}")
        print("\n故障排除建议:")
        print("1. 检查是否已安装Streamlit: pip install streamlit")
        print("2. 检查mysql_monitor.py文件是否存在")
        print("3. 尝试手动运行: streamlit run mysql_monitor.py")
        print(f"4. 尝试其他端口: streamlit run mysql_monitor.py --server.port {port+1}")

def main():
    print("=" * 50)
    print("MySQL数据库监控WebUI")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("错误: 需要Python 3.7或更高版本")
        return
    
    # 网络诊断
    available_port = diagnose_network()
    if not available_port:
        print("\n网络诊断失败，请检查网络设置")
        return
    
    # 检查依赖
    if not check_dependencies():
        return
    
    # 启动应用
    start_streamlit()

if __name__ == "__main__":
    main()
