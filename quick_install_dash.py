"""
快速安装Dash资金流向应用依赖
"""

import subprocess
import sys

def install_dash_requirements():
    """安装Dash应用必需的包"""
    
    # 核心依赖包
    essential_packages = [
        "dash>=2.14.0",
        "pandas>=1.5.0",
        "numpy>=1.21.0", 
        "plotly>=5.15.0",
        "tushare>=1.2.71",
        "akshare>=1.9.66",
        "python-dotenv>=1.0.0"
    ]
    
    print("🚀 安装Dash资金流向应用依赖包...")
    print("=" * 50)
    
    # 升级pip
    print("📦 升级pip...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    # 安装核心包
    for package in essential_packages:
        print(f"🔄 安装 {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} 安装成功")
        except subprocess.CalledProcessError:
            print(f"❌ {package} 安装失败，跳过...")
    
    print("\n🎉 核心依赖安装完成!")
    print("\n📋 安装的包:")
    for package in essential_packages:
        print(f"  - {package}")
    
    print("\n🚀 现在可以运行:")
    print("  python demo/dash_app/demo_money_flow.py")
    print("\n🌐 然后访问: http://localhost:8051")

if __name__ == "__main__":
    install_dash_requirements()
