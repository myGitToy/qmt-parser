"""
MyFunds项目依赖包安装脚本
支持分组安装，避免一次性安装过多包导致冲突
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def install_package_group(group_name, packages):
    """安装一组包"""
    print(f"\n📦 安装 {group_name}...")
    print("-" * 50)
    
    for package in packages:
        print(f"🔄 安装 {package}...")
        success, stdout, stderr = run_command(f"pip install {package}")
        
        if success:
            print(f"✅ {package} 安装成功")
        else:
            print(f"❌ {package} 安装失败: {stderr}")
            # 继续安装其他包，不中断
    
    print(f"📋 {group_name} 安装完成")

def main():
    """主安装函数"""
    print("🚀 MyFunds项目依赖包安装程序")
    print("=" * 50)
    
    # 检查pip版本
    print("🔍 检查pip版本...")
    success, stdout, stderr = run_command("pip --version")
    if success:
        print(f"✅ pip版本: {stdout.strip()}")
    else:
        print("❌ pip未找到，请先安装Python和pip")
        return
    
    # 升级pip
    print("\n🔄 升级pip...")
    run_command("pip install --upgrade pip")
    
    # 分组安装包
    package_groups = {
        "基础数据处理": [
            "numpy>=1.21.4",
            "pandas>=1.5.0", 
            "scipy>=1.9.0",
            "python-dateutil>=2.8.0",
            "pytz>=2022.1"
        ],
        
        "金融数据源": [
            "tushare>=1.2.71",
            "akshare>=1.9.66",
            "jqdatasdk>=1.8.10"
        ],
        
        "Web应用框架": [
            "dash>=2.14.0",
            "streamlit>=1.28.0", 
            "flask>=2.3.0"
        ],
        
        "数据可视化": [
            "plotly>=5.15.0",
            "matplotlib>=3.5.0",
            "seaborn>=0.11.0"
        ],
        
        "量化交易": [
            "backtrader>=1.9.76.123",
            "TA-Lib>=0.4.21"  # 注意：可能需要预编译版本
        ],
        
        "机器学习": [
            "scikit-learn>=1.1.0",
            "xgboost>=1.6.0",
            "lightgbm>=3.3.0"
        ],
        
        "数据库存储": [
            "sqlalchemy>=1.4.0",
            "pymysql>=1.0.0",
            "redis>=4.0.0",
            "h5py>=3.8.0"
        ],
        
        "文档处理": [
            "openpyxl>=3.0.0",
            "xlrd>=2.0.0",
            "python-docx>=0.8.11"
        ],
        
        "Google集成": [
            "gspread>=5.10.0",
            "google-auth>=2.20.0",
            "google-auth-oauthlib>=1.0.0"
        ],
        
        "工具库": [
            "requests>=2.28.0",
            "beautifulsoup4>=4.11.0",
            "python-dotenv>=1.0.0",
            "tqdm>=4.64.0",
            "loguru>=0.7.0"
        ]
    }
    
    # 询问用户要安装哪些包组
    print("\n📋 可用的包组:")
    for i, group_name in enumerate(package_groups.keys(), 1):
        print(f"  {i}. {group_name}")
    print(f"  {len(package_groups) + 1}. 全部安装")
    print(f"  {len(package_groups) + 2}. 仅安装Dash应用必需包")
    
    try:
        choice = input("\n请选择要安装的包组 (输入数字，多个数字用逗号分隔): ").strip()
        
        if not choice:
            print("❌ 未选择任何包组")
            return
        
        # 解析选择
        selected_groups = []
        
        if choice == str(len(package_groups) + 1):
            # 全部安装
            selected_groups = list(package_groups.keys())
        elif choice == str(len(package_groups) + 2):
            # 仅Dash必需包
            selected_groups = ["基础数据处理", "金融数据源", "Web应用框架", "数据可视化"]
        else:
            # 解析多选
            try:
                indices = [int(x.strip()) for x in choice.split(',')]
                group_names = list(package_groups.keys())
                selected_groups = [group_names[i-1] for i in indices if 1 <= i <= len(group_names)]
            except (ValueError, IndexError):
                print("❌ 输入格式错误")
                return
        
        if not selected_groups:
            print("❌ 未选择有效的包组")
            return
        
        # 安装选定的包组
        for group_name in selected_groups:
            install_package_group(group_name, package_groups[group_name])
        
        print("\n🎉 安装完成!")
        print("\n💡 特别说明:")
        print("- 如果TA-Lib安装失败，请下载预编译版本")
        print("- Windows用户: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib")
        print("- 部分包可能需要额外的系统依赖")
        
        print("\n🚀 下一步:")
        print("1. 运行 python demo/dash_app/demo_money_flow.py 测试Dash应用")
        print("2. 运行 python bloomberg_terminal/demo_simple.py 测试Bloomberg终端")
        print("3. 查看项目文档了解更多功能")
        
    except KeyboardInterrupt:
        print("\n\n👋 安装已取消")
    except Exception as e:
        print(f"\n❌ 安装过程出错: {e}")

if __name__ == "__main__":
    main()
