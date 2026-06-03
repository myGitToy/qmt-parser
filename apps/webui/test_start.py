# -*- coding: utf-8 -*-
"""
简化测试版启动脚本
"""
import os
import sys
import subprocess
from pathlib import Path

# 修复编码
if sys.platform == "win32":
    import io
    sys.stdout.reconfigure(encoding='utf-8')

PROJECT_DIR = Path(__file__).parent / "securities-dashboard"
FRONTEND_DIR = PROJECT_DIR / "frontend" / "client-web"
BACKEND_DIR = PROJECT_DIR / "backend" / "api"

FRONTEND_PORT = 5073
BACKEND_PORT = 8011

PYTHON_EXE = r"C:\Users\george\anaconda3\envs\conda_myfund\python.exe"

def main():
    print("=" * 60)
    print("证券看板平台 - 一键启动服务")
    print("=" * 60)
    print(f"前端地址: http://localhost:{FRONTEND_PORT}")
    print(f"后端 API: http://localhost:{BACKEND_PORT}")
    print("=" * 60)
    print()

    print(f"项目目录: {PROJECT_DIR}")
    print(f"前端目录: {FRONTEND_DIR}")
    print(f"后端目录: {BACKEND_DIR}")
    print(f"Python: {PYTHON_EXE}")
    print()

    # 检查目录
    if not BACKEND_DIR.exists():
        print(f"错误: 后端目录不存在: {BACKEND_DIR}")
        return 1

    if not FRONTEND_DIR.exists():
        print(f"错误: 前端目录不存在: {FRONTEND_DIR}")
        return 1

    print("开始启动服务...")
    print("按 Ctrl+C 停止服务")
    print()

    # 启动后端
    backend_proc = subprocess.Popen(
        [PYTHON_EXE, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(BACKEND_PORT), "--reload"],
        cwd=BACKEND_DIR,
    )

    print(f"✓ 后端启动成功 (PID: {backend_proc.pid})")

    # 启动前端
    vite_cmd = FRONTEND_DIR / "node_modules" / ".bin" / "vite.cmd"
    if vite_cmd.exists():
        frontend_proc = subprocess.Popen([str(vite_cmd)], cwd=FRONTEND_DIR)
    else:
        frontend_proc = subprocess.Popen(["npm", "run", "dev"], cwd=FRONTEND_DIR)

    print(f"✓ 前端启动成功 (PID: {frontend_proc.pid})")
    print()

    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("服务已停止")

    return 0

if __name__ == "__main__":
    sys.exit(main())
