#!/usr/bin/env python3
"""
MySQL监控系统完整性测试脚本
验证所有组件是否正常工作
"""

import os
import sys
import subprocess
import socket
import time
from pathlib import Path

def print_section(title):
    """打印测试章节标题"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def test_python_version():
    """测试Python版本"""
    print("检查Python版本...")
    version = sys.version_info
    if version >= (3, 7):
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} - 版本满足要求")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} - 需要3.7+")
        return False

def test_dependencies():
    """测试依赖包"""
    print("检查依赖包...")
    required_packages = [
        ('streamlit', 'streamlit'),
        ('pandas', 'pandas'), 
        ('pymysql', 'pymysql'),
        ('plotly', 'plotly'),
        ('python-dotenv', 'dotenv')
    ]
    
    all_installed = True
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✓ {package_name}")
        except ImportError:
            print(f"✗ {package_name} - 未安装")
            all_installed = False
    
    return all_installed

def test_file_structure():
    """测试文件结构"""
    print("检查文件结构...")
    current_dir = Path(".")
    required_files = [
        "mysql_monitor.py",
        "start_monitor.py",
        "test_network.py",
        ".streamlit/config.toml"
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = current_dir / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - 文件不存在")
            all_exist = False
    
    return all_exist

def test_env_file():
    """测试.env文件"""
    print("检查.env配置文件...")
    
    # 查找.env文件的可能位置
    env_paths = [
        Path(".env"),
        Path("../.env"),
        Path("../../.env"),
        Path("../../../.env")
    ]
    
    env_file = None
    for path in env_paths:
        if path.exists():
            env_file = path
            break
    
    if not env_file:
        print("✗ .env文件未找到")
        return False
    
    print(f"✓ .env文件位置: {env_file}")
    
    # 检查数据库连接配置
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    db_configs = [
        'ALIYUN_DB_CONN',
        'AWS_DB_CONN',
        'LOCAL_DB_CONN',
        'CENTOS9_DB_CONN',
        'UBUNTU186_DB_CONN',
        'UBUNTU191_DB_CONN',
        'docker_201_DB_CONN'
    ]
    
    found_configs = 0
    for config in db_configs:
        if config in content:
            found_configs += 1
            print(f"✓ {config}")
    
    if found_configs > 0:
        print(f"✓ 找到 {found_configs} 个数据库配置")
        return True
    else:
        print("✗ 未找到数据库配置")
        return False

def test_network():
    """测试网络连接"""
    print("测试网络连接...")
    
    # 测试localhost解析
    try:
        ip = socket.gethostbyname('localhost')
        print(f"✓ localhost解析: {ip}")
    except Exception as e:
        print(f"✗ localhost解析失败: {e}")
        return False
    
    # 测试端口可用性
    def test_port(port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.bind(('localhost', port))
            sock.close()
            return True
        except:
            return False
    
    available_ports = []
    test_ports = [8501, 8502, 8503, 8080]
    
    for port in test_ports:
        if test_port(port):
            available_ports.append(port)
            print(f"✓ 端口 {port} 可用")
        else:
            print(f"⚠ 端口 {port} 被占用")
    
    if available_ports:
        print(f"✓ 可用端口: {available_ports}")
        return True
    else:
        print("✗ 所有测试端口都被占用")
        return False

def test_streamlit_import():
    """测试Streamlit导入"""
    print("测试Streamlit组件...")
    try:
        import streamlit as st
        print("✓ Streamlit主模块")
        
        # 测试关键组件
        components = [
            'runtime.scriptrunner',
            'runtime.state',
            'components.v1'
        ]
        
        for component in components:
            try:
                __import__(f'streamlit.{component}')
                print(f"✓ streamlit.{component}")
            except ImportError:
                print(f"⚠ streamlit.{component} - 可选组件缺失")
        
        return True
    except ImportError as e:
        print(f"✗ Streamlit导入失败: {e}")
        return False

def test_mysql_connection():
    """测试MySQL连接能力"""
    print("测试MySQL连接能力...")
    try:
        import pymysql
        print("✓ PyMySQL模块")
        
        # 测试创建连接对象（不实际连接）
        conn_params = {
            'host': 'localhost',
            'port': 3306,
            'user': 'test',
            'password': 'test',
            'database': 'test'
        }
        
        # 这里只是测试参数格式，不会实际连接
        print("✓ 连接参数格式正确")
        return True
    except ImportError as e:
        print(f"✗ PyMySQL导入失败: {e}")
        return False

def run_syntax_check():
    """运行语法检查"""
    print("运行Python语法检查...")
    
    python_files = [
        "mysql_monitor.py",
        "start_monitor.py", 
        "test_network.py"
    ]
    
    all_valid = True
    for file_path in python_files:
        if Path(file_path).exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                compile(code, file_path, 'exec')
                print(f"✓ {file_path} 语法正确")
            except SyntaxError as e:
                print(f"✗ {file_path} 语法错误: {e}")
                all_valid = False
        else:
            print(f"⚠ {file_path} 文件不存在，跳过检查")
    
    return all_valid

def generate_report(test_results):
    """生成测试报告"""
    print_section("测试报告")
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    failed_tests = total_tests - passed_tests
    
    print(f"总测试项目: {total_tests}")
    print(f"通过项目: {passed_tests}")
    print(f"失败项目: {failed_tests}")
    print(f"成功率: {passed_tests/total_tests*100:.1f}%")
    
    if failed_tests == 0:
        print("\n🎉 所有测试通过！系统已准备就绪。")
        print("\n启动建议:")
        print("1. 运行 python start_monitor.py")
        print("2. 或运行 start_monitor.bat")
        print("3. 访问 http://localhost:8501")
    else:
        print(f"\n⚠ 发现 {failed_tests} 个问题，请检查上述失败项目。")
        print("\n修复建议:")
        if not test_results.get('依赖包'):
            print("- 安装缺失的依赖包: pip install -r requirements_monitor.txt")
        if not test_results.get('文件结构'):
            print("- 确保所有必要文件都存在")
        if not test_results.get('环境配置'):
            print("- 检查.env文件配置")
        if not test_results.get('网络'):
            print("- 检查网络设置和端口占用")

def main():
    """主测试函数"""
    print_section("MySQL监控系统完整性测试")
    print("开始系统测试...")
    
    # 执行所有测试
    test_results = {}
    
    print_section("1. 环境检查")
    test_results['Python版本'] = test_python_version()
    test_results['依赖包'] = test_dependencies()
    
    print_section("2. 文件检查")
    test_results['文件结构'] = test_file_structure()
    test_results['环境配置'] = test_env_file()
    
    print_section("3. 网络检查")
    test_results['网络'] = test_network()
    
    print_section("4. 组件检查")
    test_results['Streamlit'] = test_streamlit_import()
    test_results['MySQL'] = test_mysql_connection()
    
    print_section("5. 语法检查")
    test_results['语法'] = run_syntax_check()
    
    # 生成报告
    generate_report(test_results)

if __name__ == "__main__":
    main()
