"""
Celery Worker 启动脚本
用于启动消息队列工作进程
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def start_celery_worker():
    """启动 Celery Worker"""
    
    # 添加当前目录到 Python 路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    print("🚀 启动 Celery Worker")
    print("=" * 50)
    
    # 检查 Redis 是否可用
    print("🔍 检查 Redis 连接...")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis 连接正常")
    except Exception as e:
        print(f"❌ Redis 连接失败: {e}")
        print("请确保 Redis 服务正在运行")
        return False
    
    # 设置环境变量
    env = os.environ.copy()
    env['PYTHONPATH'] = current_dir
    
    # Celery Worker 命令
    cmd = [
        sys.executable, '-m', 'celery',
        '-A', 'celery_handler:CeleryHandler.app',
        'worker',
        '--loglevel=info',
        '--concurrency=4',
        '--queues=default,long_tasks,batch',
        '--hostname=worker@%h'
    ]
    
    print(f"🔧 执行命令: {' '.join(cmd)}")
    print("💡 提示: 按 Ctrl+C 停止 Worker")
    print("-" * 50)
    
    try:
        # 启动 Celery Worker
        process = subprocess.Popen(
            cmd,
            env=env,
            cwd=current_dir
        )
        
        # 等待进程结束
        process.wait()
        
    except KeyboardInterrupt:
        print("\n⛔ 收到停止信号，正在关闭 Worker...")
        if process:
            process.terminate()
            time.sleep(2)
            if process.poll() is None:
                process.kill()
        print("✅ Worker 已停止")
        
    except Exception as e:
        print(f"❌ 启动 Worker 失败: {e}")
        return False
    
    return True

def start_celery_beat():
    """启动 Celery Beat 调度器"""
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("⏰ 启动 Celery Beat 调度器")
    print("=" * 50)
    
    # 设置环境变量
    env = os.environ.copy()
    env['PYTHONPATH'] = current_dir
    
    # Celery Beat 命令
    cmd = [
        sys.executable, '-m', 'celery',
        '-A', 'celery_handler:CeleryHandler.app',
        'beat',
        '--loglevel=info'
    ]
    
    print(f"🔧 执行命令: {' '.join(cmd)}")
    print("💡 提示: 按 Ctrl+C 停止 Beat")
    print("-" * 50)
    
    try:
        # 启动 Celery Beat
        process = subprocess.Popen(
            cmd,
            env=env,
            cwd=current_dir
        )
        
        # 等待进程结束
        process.wait()
        
    except KeyboardInterrupt:
        print("\n⛔ 收到停止信号，正在关闭 Beat...")
        if process:
            process.terminate()
            time.sleep(2)
            if process.poll() is None:
                process.kill()
        print("✅ Beat 已停止")
        
    except Exception as e:
        print(f"❌ 启动 Beat 失败: {e}")
        return False
    
    return True

def show_celery_status():
    """显示 Celery 状态"""
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("📊 Celery 状态检查")
    print("=" * 50)
    
    # 设置环境变量
    env = os.environ.copy()
    env['PYTHONPATH'] = current_dir
    
    # 检查活动的 Workers
    cmd = [
        sys.executable, '-m', 'celery',
        '-A', 'celery_handler:CeleryHandler.app',
        'inspect', 'active'
    ]
    
    try:
        result = subprocess.run(cmd, env=env, cwd=current_dir, capture_output=True, text=True)
        print("🏃 活动任务:")
        print(result.stdout)
        
    except Exception as e:
        print(f"❌ 检查状态失败: {e}")

def main():
    """主函数"""
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python start_celery.py worker   # 启动 Worker")
        print("  python start_celery.py beat     # 启动 Beat 调度器")
        print("  python start_celery.py status   # 查看状态")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'worker':
        start_celery_worker()
    elif command == 'beat':
        start_celery_beat()
    elif command == 'status':
        show_celery_status()
    else:
        print(f"❌ 未知命令: {command}")
        print("支持的命令: worker, beat, status")

if __name__ == "__main__":
    main()
