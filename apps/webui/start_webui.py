#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
证券看板一键启动脚本
启动前端和后端服务
功能：
- 端口占用检测并强制终止占用进程
- 自动重启进程（崩溃时）
- 监听进程状态
"""

import os
import sys
import subprocess
import threading
import time
import signal
import psutil
import warnings
from pathlib import Path

# 抑制 requests 库的依赖版本警告（可选）
warnings.filterwarnings("ignore", message=".*doesn't match a supported version.*")

# 修复 Windows 控制台编码问题
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

# 加载环境变量
WEBUI_DIR = Path(__file__).parent
ENV_FILE = WEBUI_DIR / ".env"
if ENV_FILE.exists():
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE)
    print(f"✓ 已加载环境变量: {ENV_FILE}")

# 项目配置
PROJECT_DIR = WEBUI_DIR / "securities-dashboard"
FRONTEND_DIR = PROJECT_DIR / "frontend" / "client-web"
BACKEND_DIR = PROJECT_DIR / "backend" / "api"

# 平台适配：Windows 用 npm.cmd，Unix 用 npm
NPM_CMD = "npm.cmd" if sys.platform == "win32" else "npm"

# 端口配置
FRONTEND_PORT = 5073
BACKEND_PORT = 8011
# 5074 端口预留，可用于 WebSocket 或其他服务

# 进程列表
processes = []
shutdown_event = threading.Event()

# 查找正确的 Python 解释器（带有 uvicorn 的）
def find_python_with_uvicorn():
    """查找安装了 uvicorn 的 Python 解释器"""
    # 尝试常见的 Python 路径（优先 anaconda 环境）
    common_paths = [
        r"C:\Users\george\anaconda3\envs\conda_myfund\python.exe",
        r"C:\Users\george\anaconda3\python.exe",
        r"C:\Python314\python.exe",
        r"C:\Python313\python.exe",
        r"C:\Python312\python.exe",
    ]

    for path in common_paths:
        if os.path.exists(path):
            try:
                result = subprocess.run(
                    [path, "-c", "import uvicorn"],
                    capture_output=True,
                    check=False,
                )
                if result.returncode == 0:
                    return path
            except:
                pass

    # 回退到当前 Python
    try:
        import uvicorn
        return sys.executable
    except ImportError:
        pass

    return sys.executable

PYTHON_EXE = find_python_with_uvicorn()


def kill_process_on_port(port: int) -> bool:
    """
    查找并终止占用指定端口的进程

    Args:
        port: 端口号

    Returns:
        bool: 是否成功终止进程
    """
    killed = False
    try:
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == 'LISTEN':
                try:
                    process = psutil.Process(conn.pid)
                    print(f"  🗑️  发现端口 {port} 被进程 {conn.pid} 占用: {process.name()}")
                    process.terminate()
                    process.wait(timeout=5)
                    print(f"  ✅ 已终止进程 {conn.pid}")
                    killed = True
                except psutil.NoSuchProcess:
                    print(f"  ⚠️  进程 {conn.pid} 不存在")
                except psutil.AccessDenied:
                    print(f"  ⚠️  无权限终止进程 {conn.pid}，尝试强制终止...")
                    try:
                        process.kill()
                        killed = True
                        print(f"  ✅ 已强制终止进程 {conn.pid}")
                    except:
                        print(f"  ❌ 无法终止进程 {conn.pid}")
                except subprocess.TimeoutExpired:
                    print(f"  ⚠️  进程 {conn.pid} 超时未退出，尝试强制终止...")
                    try:
                        process.kill()
                        killed = True
                        print(f"  ✅ 已强制终止进程 {conn.pid}")
                    except:
                        print(f"  ❌ 无法强制终止进程 {conn.pid}")
    except Exception as e:
        print(f"  ❌ 检测端口时出错: {e}")
    return killed


def check_and_clear_ports():
    """检查并清理被占用的端口"""
    print("🔍 检查端口占用...")

    ports_to_check = [FRONTEND_PORT, BACKEND_PORT]
    for port in ports_to_check:
        if kill_process_on_port(port):
            print(f"  ✅ 端口 {port} 已清理")
        else:
            print(f"  ✓ 端口 {port} 空闲")

    # 等待端口完全释放
    time.sleep(1)


def print_banner():
    """打印启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║           证券看板平台 - 一键启动服务                      ║
    ╠══════════════════════════════════════════════════════════╣
    ║  前端地址: http://localhost:{}                            ║
    ║  后端 API: http://localhost:{}                             ║
    ╚══════════════════════════════════════════════════════════╝
    """.format(FRONTEND_PORT, BACKEND_PORT)
    print(banner, flush=True)


def check_dependencies():
    """检查依赖是否安装"""
    print("🔍 检查依赖...")

    # 检查 psutil
    try:
        import psutil
        print(f"  ✓ psutil {psutil.__version__}")
    except ImportError:
        print("  ✗ psutil 未安装")
        print("  📦 正在安装 psutil...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "psutil"],
            check=True,
        )
        print("  ✓ psutil 安装完成")

    # 检查 Node.js
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            print(f"  ✓ Node.js {result.stdout.strip()}")
        else:
            print("  ✗ Node.js 未安装")
            return False
    except FileNotFoundError:
        print("  ✗ Node.js 未找到")
        return False

    # 检查 npm
    try:
        result = subprocess.run(
            [NPM_CMD, "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            print(f"  ✓ npm {result.stdout.strip()}")
        else:
            print("  ⚠ npm 未找到，但前端依赖已安装")
    except FileNotFoundError:
        print("  ⚠ npm 未找到，但前端依赖已安装")

    # 检查 Python
    try:
        result = subprocess.run(
            ["python", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            print(f"  ✓ Python {result.stdout.strip()}")
        else:
            print("  ✗ Python 未安装")
            return False
    except FileNotFoundError:
        print("  ✗ Python 未找到")
        return False

    # 检查前端 node_modules
    ensure_npm_deps()
    print("  ✓ 前端依赖已安装")

    # 检查后端 Python 包
    try:
        import fastapi
        import tushare
        print("  ✓ 后端依赖已安装")
    except ImportError:
        # 尝试通过 pip 检查
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list"],
            capture_output=True,
            text=True,
            check=False,
        )
        if "fastapi" in result.stdout.lower() and "tushare" in result.stdout.lower():
            print("  ✓ 后端依赖已安装")
        else:
            print("  ⚠ 后端依赖可能未安装，尝试启动可能会失败")
            print("    如有问题，请运行: pip install -r requirements.txt")

    return True


def ensure_npm_deps() -> None:
    """确保前端依赖已安装，缺失则自动安装（参考 HMU start_all.py）"""
    node_modules = FRONTEND_DIR / "node_modules"
    if node_modules.exists():
        return
    print(f"  📦 检测到缺少 node_modules，正在安装前端依赖...")
    result = subprocess.run(
        [NPM_CMD, "install"],
        cwd=str(FRONTEND_DIR),
    )
    if result.returncode != 0:
        print("  ❌ 前端依赖安装失败")
        sys.exit(1)
    print("  ✓ 前端依赖安装完成")


def start_backend():
    """启动后端服务"""
    print(f"🚀 启动后端服务 (端口 {BACKEND_PORT})...")
    print(f"   使用 Python: {PYTHON_EXE}")

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PORT"] = str(BACKEND_PORT)

    proc = subprocess.Popen(
        [
            PYTHON_EXE,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(BACKEND_PORT),
            "--reload",
        ],
        cwd=BACKEND_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,  # 行缓冲
    )

    processes.append(("Backend", proc))
    return proc


def start_frontend():
    """启动前端服务"""
    print(f"🎨 启动前端服务 (端口 {FRONTEND_PORT})...")

    env = os.environ.copy()
    env["PORT"] = str(FRONTEND_PORT)

    # 优先使用 npm，其次使用 npx，最后直接运行 vite
    vite_path = FRONTEND_DIR / "node_modules" / ".bin" / "vite.cmd"
    if vite_path.exists():
        # Windows 下直接使用 vite
        proc = subprocess.Popen(
            [str(vite_path)],
            cwd=FRONTEND_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    else:
        # 使用 npm run dev
        proc = subprocess.Popen(
            [NPM_CMD, "run", "dev"],
            cwd=FRONTEND_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

    processes.append(("Frontend", proc))
    return proc


def monitor_process(name, proc):
    """监控进程输出"""
    try:
        for line in iter(proc.stdout.readline, ""):
            if shutdown_event.is_set():
                break
            if line:
                print(f"[{name}] {line.rstrip()}")
    except:
        pass


def signal_handler(signum, frame):
    """信号处理器"""
    print("\n\n⏹️  接收到停止信号，正在关闭服务...")
    shutdown_event.set()
    stop_all()
    sys.exit(0)


def stop_all():
    """停止所有服务"""
    for name, proc in processes:
        try:
            print(f"  🛑 停止 {name}...")
            proc.terminate()
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        except:
            pass


def main():
    """主函数"""
    print_banner()

    # 切换到项目目录
    os.chdir(PROJECT_DIR)

    # 检查并清理端口占用
    check_and_clear_ports()

    # 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请安装缺失的依赖后重试")
        return 1

    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 启动服务
    print("\n⏳ 启动服务中...")

    # 启动后端
    backend_proc = start_backend()
    threading.Thread(
        target=monitor_process, args=("Backend", backend_proc), daemon=True
    ).start()
    time.sleep(2)  # 等待后端启动

    # 启动前端
    frontend_proc = start_frontend()
    threading.Thread(
        target=monitor_process, args=("Frontend", frontend_proc), daemon=True
    ).start()

    print(f"\n✅ 所有服务已启动！")
    print(f"   前端: http://localhost:{FRONTEND_PORT}")
    print(f"   后端: http://localhost:{BACKEND_PORT}/docs")
    print(f"\n🔄 启用自动重启：如果服务崩溃将自动重启")
    print(f"\n按 Ctrl+C 停止所有服务\n")

    # 等待进程并实现自动重启
    try:
        while True:
            # 检查进程状态
            for i, (name, proc) in enumerate(processes[:]):
                if proc.poll() is not None:
                    exit_code = proc.returncode
                    print(f"\n⚠️  {name} 已意外停止，退出码: {exit_code}")
                    print(f"🔄 正在尝试重启 {name}...")

                    # 移除旧进程
                    processes.pop(i)

                    # 重启对应服务
                    if name == "Backend":
                        time.sleep(2)  # 等待端口释放
                        new_proc = start_backend()
                        processes.append(("Backend", new_proc))
                        threading.Thread(
                            target=monitor_process, args=("Backend", new_proc), daemon=True
                        ).start()
                        print(f"✅ 后端服务已重启")
                    elif name == "Frontend":
                        time.sleep(2)
                        new_proc = start_frontend()
                        processes.append(("Frontend", new_proc))
                        threading.Thread(
                            target=monitor_process, args=("Frontend", new_proc), daemon=True
                        ).start()
                        print(f"✅ 前端服务已重启")

            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)

    return 0


if __name__ == "__main__":
    sys.exit(main())
