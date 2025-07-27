"""
Bloomberg Terminal Demo - 简化启动脚本
适配当前Python环境
"""

import sys
import os
from pathlib import Path

def main():
    """简化的启动函数"""
    print("🏦 Bloomberg Terminal Demo")
    print("=" * 50)
    
    # 检查文件是否存在
    demo_file = Path("demo_simple.py")
    if not demo_file.exists():
        print("❌ 找不到 demo_simple.py 文件")
        print("请确保在 bloomberg_terminal 目录下运行")
        return
    
    print("✅ 找到应用文件")
    print("🚀 正在启动...")
    print("📱 应用将在浏览器中打开: http://localhost:8501")
    print("⏹️  按 Ctrl+C 停止应用")
    print("-" * 50)
    
    # 导入并运行Streamlit
    try:
        # 设置Streamlit配置
        os.environ['STREAMLIT_SERVER_PORT'] = '8501'
        os.environ['STREAMLIT_SERVER_ADDRESS'] = 'localhost'
        os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
        
        # 直接导入并运行demo_simple模块
        import demo_simple
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请安装必要的依赖包:")
        print("pip install streamlit plotly pandas numpy")
    except Exception as e:
        print(f"❌ 运行错误: {e}")

if __name__ == "__main__":
    main()
