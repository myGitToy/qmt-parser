#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bloomberg Terminal Demo 启动脚本
Python版本 - 可在VS Code中直接运行
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def print_banner():
    """打印启动横幅"""
    print("\n" + "="*70)
    print("               Bloomberg Terminal Demo")
    print("                金融数据终端演示平台")
    print("="*70)
    print()

def check_environment():
    """检查运行环境"""
    print("[INFO] 正在检查环境...")
    
    # 检查是否在正确目录
    current_dir = Path.cwd()
    demo_file = current_dir / "demo_simple.py"
    
    if not demo_file.exists():
        print(f"[ERROR] 在当前目录找不到 demo_simple.py")
        print(f"[ERROR] 当前目录: {current_dir}")
        print(f"[ERROR] 请确保在 bloomberg_terminal 目录下运行此脚本")
        return False
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
        print(f"[ERROR] Python版本过低: {python_version.major}.{python_version.minor}")
        print(f"[ERROR] 需要Python 3.7或更高版本")
        return False
    
    print(f"[INFO] Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    print(f"[INFO] 工作目录: {current_dir}")
    return True

def install_dependencies():
    """安装必要的依赖包"""
    required_packages = ['streamlit', 'plotly', 'pandas', 'numpy']
    missing_packages = []
    
    # 检查哪些包缺失
    for package in required_packages:
        try:
            __import__(package)
            print(f"[INFO] ✓ {package} 已安装")
        except ImportError:
            missing_packages.append(package)
            print(f"[WARN] ✗ {package} 未安装")
    
    # 安装缺失的包
    if missing_packages:
        print(f"\n[INFO] 正在安装缺失的包: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '--user'
            ] + missing_packages)
            print("[INFO] ✓ 依赖包安装完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] 依赖包安装失败: {e}")
            return False
    else:
        print("[INFO] ✓ 所有依赖包已安装")
        return True

def start_streamlit():
    """启动Streamlit应用"""
    print("\n[INFO] 正在启动Bloomberg Terminal Demo...")
    print("[INFO] 应用将在浏览器中自动打开")
    print("[INFO] 访问地址: http://localhost:8501")
    print("[INFO] 按 Ctrl+C 停止应用")
    print("\n" + "-"*50)
    
    try:
        # 启动Streamlit应用
        cmd = [
            sys.executable, '-m', 'streamlit', 'run', 'demo_simple.py',
            '--server.port', '8501',
            '--server.address', 'localhost',
            '--browser.gatherUsageStats', 'false'
        ]
        
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] 应用启动失败: {e}")
        return False
    except KeyboardInterrupt:
        print(f"\n[INFO] 应用已停止")
        return True
    
    return True

def main():
    """主函数"""
    try:
        # 设置控制台编码
        if sys.platform == 'win32':
            os.system('chcp 65001 > nul')
        
        print_banner()
        
        # 检查环境
        if not check_environment():
            input("\n按任意键退出...")
            return 1
        
        # 安装依赖
        if not install_dependencies():
            input("\n按任意键退出...")
            return 1
        
        # 启动应用
        if not start_streamlit():
            input("\n按任意键退出...")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] 意外错误: {e}")
        input("\n按任意键退出...")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
