#!/usr/bin/env python
"""
简单的 Celery 启动脚本
"""

import os
import sys
import subprocess

# 设置当前目录为 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 设置环境变量
os.environ['PYTHONPATH'] = current_dir

def start_worker():
    """启动 Worker"""
    print("正在启动 Celery Worker...")
    
    # 导入模块以确保配置正确
    try:
        from demo_celery import app
        print("✓ Celery 应用加载成功")
    except Exception as e:
        print(f"✗ Celery 应用加载失败: {e}")
        return False
    
    # 启动 worker
    try:
        from celery.bin import worker
        worker_instance = worker.worker(app=app)
        worker_instance.run(
            loglevel='info',
            concurrency=2,
            queues=['securities_update', 'batch_update']
        )
    except Exception as e:
        print(f"Worker 启动失败: {e}")
        return False
    
    return True

def start_flower():
    """启动 Flower"""
    print("正在启动 Flower 监控界面...")
    
    try:
        from demo_celery import app
        import flower
        from flower.app import Flower
        
        flower_app = Flower(app=app, port=5555)
        flower_app.start()
        
    except Exception as e:
        print(f"Flower 启动失败: {e}")
        return False
    
    return True

def main():
    if len(sys.argv) < 2:
        print("用法: python simple_start.py [worker|flower]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'worker':
        start_worker()
    elif command == 'flower':
        start_flower()
    else:
        print(f"未知命令: {command}")
        sys.exit(1)

if __name__ == '__main__':
    main()
