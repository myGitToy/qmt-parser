"""
测试 Celery 任务脚本
"""
import os
import sys
import time
from pathlib import Path

# 确保当前目录在 Python 路径中
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 导入我们的 Celery 应用
from demo_celery import app, update_single_security, batch_update_securities

def test_celery_tasks():
    """测试 Celery 任务"""
    print("=== Celery 任务测试 ===")
    
    # 测试单个任务
    print("\n1. 测试提交单个任务...")
    security_info = {
        'id': 1,
        'security_code': '000001',
        'security_name': '平安银行',
        'update_type': 'price'
    }
    
    try:
        result = update_single_security.delay(security_info)
        print(f"✓ 任务已提交，任务ID: {result.id}")
        
        # 等待任务完成
        print("等待任务完成...")
        for i in range(30):  # 最多等待30秒
            if result.ready():
                break
            time.sleep(1)
            print(f"等待中... ({i+1}/30)")
        
        if result.ready():
            if result.successful():
                print(f"✓ 任务完成: {result.result}")
            else:
                print(f"✗ 任务失败: {result.result}")
        else:
            print("⚠ 任务超时")
            
    except Exception as e:
        print(f"✗ 任务提交失败: {e}")
    
    # 测试批量任务
    print("\n2. 测试批量任务...")
    try:
        result = batch_update_securities.delay(batch_size=3)
        print(f"✓ 批量任务已提交，任务ID: {result.id}")
        
        # 等待批量任务完成
        print("等待批量任务完成...")
        for i in range(60):  # 最多等待60秒
            if result.ready():
                break
            time.sleep(1)
            print(f"等待中... ({i+1}/60)")
        
        if result.ready():
            if result.successful():
                print(f"✓ 批量任务完成: {result.result}")
            else:
                print(f"✗ 批量任务失败: {result.result}")
        else:
            print("⚠ 批量任务超时")
            
    except Exception as e:
        print(f"✗ 批量任务提交失败: {e}")

def check_celery_status():
    """检查 Celery 状态"""
    print("\n=== Celery 状态检查 ===")
    
    try:
        # 检查 Celery 连接
        inspect = app.control.inspect()
        
        # 检查活跃的 workers
        active_workers = inspect.active()
        if active_workers:
            print(f"✓ 发现活跃的 Workers: {list(active_workers.keys())}")
        else:
            print("⚠ 没有发现活跃的 Workers")
        
        # 检查队列状态
        reserved = inspect.reserved()
        if reserved:
            print(f"✓ 队列状态: {reserved}")
        else:
            print("ℹ 队列为空")
            
        return True
        
    except Exception as e:
        print(f"✗ Celery 状态检查失败: {e}")
        return False

if __name__ == '__main__':
    print("Celery 证券数据更新系统测试")
    print("=" * 50)
    
    # 检查 Celery 状态
    if check_celery_status():
        # 如果有 Workers 在运行，则测试任务
        test_celery_tasks()
    else:
        print("\n请先启动 Celery Worker:")
        print("celery -A demo_celery worker --loglevel=info")
