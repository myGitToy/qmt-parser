"""
Bloomberg Terminal Demo - 测试版本
最小化依赖，确保能正常运行
"""

import sys
import os

# 检查基本依赖
try:
    import pandas as pd
    import numpy as np
    print("✅ 数据处理库可用")
except ImportError as e:
    print(f"❌ 缺少数据处理库: {e}")
    sys.exit(1)

try:
    import streamlit as st
    print("✅ Streamlit可用")
except ImportError:
    print("❌ Streamlit未安装")
    print("请运行: pip install streamlit")
    sys.exit(1)

try:
    import plotly.graph_objects as go
    print("✅ Plotly可用")
except ImportError:
    print("❌ Plotly未安装") 
    print("请运行: pip install plotly")
    sys.exit(1)

print("🎉 所有依赖检查通过!")
print("🚀 现在可以运行应用了")
print()
print("运行命令:")
print("streamlit run demo_simple.py")
print()
print("或在VS Code中打开 demo_simple.py 并运行")

# 如果是直接运行这个脚本，尝试启动streamlit
if __name__ == "__main__":
    print("\n🔄 尝试自动启动...")
    import subprocess
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "demo_simple.py"], check=True)
    except Exception as e:
        print(f"❌ 自动启动失败: {e}")
        print("请手动运行: streamlit run demo_simple.py")
