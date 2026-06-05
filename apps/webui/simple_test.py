#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单测试脚本，验证依赖是否正常
"""

import os
import sys
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=== 测试开始 ===")

# 测试 dotenv
try:
    from dotenv import load_dotenv
    print("✓ dotenv 模块加载成功")
except ImportError as e:
    print(f"✗ dotenv 模块加载失败: {e}")
    sys.exit(1)

# 测试 uvicorn
try:
    import uvicorn
    print("✓ uvicorn 模块加载成功")
except ImportError as e:
    print(f"✗ uvicorn 模块加载失败: {e}")
    sys.exit(1)

# 测试 fastapi
try:
    import fastapi
    print("✓ fastapi 模块加载成功")
except ImportError as e:
    print(f"✗ fastapi 模块加载失败: {e}")
    sys.exit(1)

# 检查 .env 文件
WEBUI_DIR = Path(__file__).parent
ENV_FILE = WEBUI_DIR / ".env"

if ENV_FILE.exists():
    print(f"✓ 找到环境变量文件: {ENV_FILE}")
    load_dotenv(ENV_FILE)
    print("✓ 环境变量加载成功")
else:
    print(f"⚠ 未找到环境变量文件: {ENV_FILE}")
    print("将使用默认配置")

# 检查项目目录
PROJECT_DIR = WEBUI_DIR / "securities-dashboard"
FRONTEND_DIR = PROJECT_DIR / "frontend" / "client-web"
BACKEND_DIR = PROJECT_DIR / "backend" / "api"

print(f"✓ 项目目录: {PROJECT_DIR}")
print(f"✓ 前端目录: {FRONTEND_DIR}")
print(f"✓ 后端目录: {BACKEND_DIR}")

# 检查是否存在
print(f"前端目录存在: {FRONTEND_DIR.exists()}")
print(f"后端目录存在: {BACKEND_DIR.exists()}")

print("\n=== 测试完成 ===")