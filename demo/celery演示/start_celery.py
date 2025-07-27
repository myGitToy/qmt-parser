"""
启动脚本和管理命令
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

class CeleryManager:
    """Celery 管理器"""
    
    def __init__(self):
        self.worker_processes = []
        self.beat_process = None
        self.flower_process = None
    
    def start_worker(self, concurrency=4, queues=None):
        """启动 Celery Worker"""
        if queues is None:
            queues = ['securities_update', 'batch_update']
        
        queue_str = ','.join(queues)
        
        cmd = [
            'celery', '-A', 'demo_celery', 'worker',
            '--loglevel=info',
            f'--concurrency={concurrency}',
            f'--queues={queue_str}',
            '--prefetch-multiplier=1'
        ]
        
        print(f"启动 Celery Worker: {' '.join(cmd)}")
        process = subprocess.Popen(cmd)
        self.worker_processes.append(process)
        return process
    
    def start_beat(self):
        """启动 Celery Beat (定时任务调度器)"""
        cmd = [
            'celery', '-A', 'demo_celery', 'beat',
            '--loglevel=info'
        ]
        
        print(f"启动 Celery Beat: {' '.join(cmd)}")
        self.beat_process = subprocess.Popen(cmd)
        return self.beat_process
    
    def start_flower(self, port=5555):
        """启动 Flower (监控界面)"""
        cmd = [
            'celery', '-A', 'demo_celery', 'flower',
            f'--port={port}'
        ]
        
        print(f"启动 Flower: {' '.join(cmd)}")
        self.flower_process = subprocess.Popen(cmd)
        return self.flower_process
    
    def stop_all(self):
        """停止所有进程"""
        print("正在停止所有 Celery 进程...")
        
        # 停止 workers
        for process in self.worker_processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
        
        # 停止 beat
        if self.beat_process and self.beat_process.poll() is None:
            self.beat_process.terminate()
            try:
                self.beat_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.beat_process.kill()
        
        # 停止 flower
        if self.flower_process and self.flower_process.poll() is None:
            self.flower_process.terminate()
            try:
                self.flower_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.flower_process.kill()
        
        print("所有进程已停止")
    
    def status(self):
        """检查进程状态"""
        print("=== Celery 进程状态 ===")
        
        print(f"Worker 进程: {len(self.worker_processes)} 个")
        for i, process in enumerate(self.worker_processes):
            status = "运行中" if process.poll() is None else "已停止"
            print(f"  Worker {i+1}: {status} (PID: {process.pid})")
        
        if self.beat_process:
            status = "运行中" if self.beat_process.poll() is None else "已停止"
            print(f"Beat 进程: {status} (PID: {self.beat_process.pid})")
        else:
            print("Beat 进程: 未启动")
        
        if self.flower_process:
            status = "运行中" if self.flower_process.poll() is None else "已停止"
            print(f"Flower 进程: {status} (PID: {self.flower_process.pid})")
        else:
            print("Flower 进程: 未启动")


def signal_handler(signum, frame):
    """信号处理器"""
    print(f"\n收到信号 {signum}，正在停止...")
    if hasattr(signal_handler, 'manager'):
        signal_handler.manager.stop_all()
    sys.exit(0)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python start_celery.py [worker|beat|flower|all|stop|status]")
        sys.exit(1)
    
    manager = CeleryManager()
    signal_handler.manager = manager
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    command = sys.argv[1].lower()
    
    if command == 'worker':
        concurrency = int(sys.argv[2]) if len(sys.argv) > 2 else 4
        manager.start_worker(concurrency=concurrency)
        print("Worker 已启动，按 Ctrl+C 停止")
        
    elif command == 'beat':
        manager.start_beat()
        print("Beat 已启动，按 Ctrl+C 停止")
        
    elif command == 'flower':
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 5555
        manager.start_flower(port=port)
        print(f"Flower 已启动，访问 http://localhost:{port}")
        
    elif command == 'all':
        manager.start_worker(concurrency=4)
        time.sleep(2)
        manager.start_beat()
        time.sleep(2)
        manager.start_flower()
        print("所有服务已启动")
        print("- Worker: 处理任务")
        print("- Beat: 定时任务调度")
        print("- Flower: 监控界面 http://localhost:5555")
        
    elif command == 'stop':
        manager.stop_all()
        return
        
    elif command == 'status':
        manager.status()
        return
        
    else:
        print(f"未知命令: {command}")
        sys.exit(1)
    
    try:
        # 保持进程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
