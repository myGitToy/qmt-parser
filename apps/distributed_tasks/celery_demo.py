"""
CeleryHandler使用演示脚本
展示消息队列的基础操作方法
"""

import sys
import os
import time
import json
from datetime import datetime

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from celery_handler import CeleryHandler
except ImportError:
    print("无法导入 CeleryHandler，请确保文件存在")
    sys.exit(1)

def demo_queue_operations():
    """演示队列基础操作"""
    print("🚀 开始演示 Celery 消息队列基础操作")
    print("=" * 60)
    
    # 创建 CeleryHandler 实例
    handler = CeleryHandler()
    
    # === 1. 简单任务演示 ===
    print("\n📋 1. 简单任务演示")
    print("-" * 30)
    
    # 提交简单任务
    task_id = handler.submit_simple_task("测试消息", delay=3)
    print(f"✅ 提交简单任务: {task_id}")
    
    # 检查任务状态
    print("⏳ 检查任务状态...")
    for i in range(5):
        status = handler.get_task_status(task_id)
        print(f"  状态: {status['state']}")
        if status.get('ready'):
            break
        time.sleep(1)
    
    # 等待任务完成
    print("⌛ 等待任务完成...")
    result = handler.wait_for_task(task_id, timeout=10)
    print(f"✨ 任务结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    # === 2. 批量任务演示 ===
    print("\n📦 2. 批量任务演示")
    print("-" * 30)
    
    items = [f"数据项_{i:03d}" for i in range(1, 21)]  # 20个数据项
    batch_task_id = handler.submit_batch_task(items, batch_size=5)
    print(f"✅ 提交批量任务: {batch_task_id}")
    print(f"📊 处理 {len(items)} 个项目，批次大小: 5")
    
    # 监控批量任务进度
    print("⏳ 监控批量任务进度...")
    start_time = time.time()
    while time.time() - start_time < 60:  # 最多等待60秒
        status = handler.get_task_status(batch_task_id)
        state = status.get('state', 'UNKNOWN')
        
        if state == 'PROGRESS':
            progress = status.get('progress', {})
            percentage = progress.get('percentage', 0)
            message = progress.get('message', '处理中...')
            current_batch = progress.get('current_batch', 0)
            total_batches = progress.get('total_batches', 0)
            
            print(f"  📈 {message} - {percentage}% ({current_batch}/{total_batches} 批次)")
            
        elif state in ['SUCCESS', 'FAILURE']:
            print(f"✨ 批量任务完成: {state}")
            if state == 'SUCCESS':
                result = status.get('result', {})
                print(f"📋 处理了 {result.get('processed_items', 0)} 个项目")
            break
        else:
            print(f"  状态: {state}")
        
        time.sleep(2)
    
    # === 3. 长时间任务演示 ===
    print("\n⏰ 3. 长时间任务演示")
    print("-" * 30)
    
    long_task_id = handler.submit_long_task(duration=15, progress_updates=True)
    print(f"✅ 提交长时间任务: {long_task_id}")
    print("📊 预计运行 15 秒，每5秒更新进度")
    
    # 监控长时间任务
    print("⏳ 监控长时间任务进度...")
    start_time = time.time()
    while time.time() - start_time < 30:  # 最多等待30秒
        status = handler.get_task_status(long_task_id)
        state = status.get('state', 'UNKNOWN')
        
        if state == 'PROGRESS':
            progress = status.get('progress', {})
            percentage = progress.get('percentage', 0)
            current = progress.get('current', 0)
            total = progress.get('total', 0)
            
            print(f"  🔄 进度: {percentage}% ({current}/{total} 秒)")
            
        elif state in ['SUCCESS', 'FAILURE']:
            print(f"✨ 长时间任务完成: {state}")
            break
        else:
            print(f"  状态: {state}")
        
        time.sleep(3)
    
    # === 4. 错误处理和重试演示 ===
    print("\n🔄 4. 错误处理和重试演示")
    print("-" * 30)
    
    error_task_id = handler.submit_error_task(should_fail=True, error_message="演示重试机制")
    print(f"✅ 提交错误任务: {error_task_id}")
    print("🎯 该任务会故意失败并重试")
    
    # 监控错误任务重试过程
    print("⏳ 监控重试过程...")
    start_time = time.time()
    retry_count = 0
    while time.time() - start_time < 45:  # 最多等待45秒
        status = handler.get_task_status(error_task_id)
        state = status.get('state', 'UNKNOWN')
        
        if state == 'RETRY':
            retry_count += 1
            print(f"  🔄 任务重试中... (第 {retry_count} 次)")
        elif state == 'SUCCESS':
            print(f"✨ 任务最终成功! (经过 {retry_count} 次重试)")
            result = status.get('result', {})
            print(f"📋 结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            break
        elif state == 'FAILURE':
            print(f"❌ 任务最终失败")
            break
        else:
            print(f"  状态: {state}")
        
        time.sleep(3)
    
    # === 5. 队列信息查看 ===
    print("\n📊 5. 队列信息查看")
    print("-" * 30)
    
    queue_info = handler.get_queue_info()
    print("📈 当前队列状态:")
    
    active_tasks = queue_info.get('active_tasks', {})
    if active_tasks:
        total_active = sum(len(tasks) for tasks in active_tasks.values())
        print(f"  🏃 活动任务: {total_active} 个")
    else:
        print("  🏃 活动任务: 0 个")
    
    scheduled_tasks = queue_info.get('scheduled_tasks', {})
    if scheduled_tasks:
        total_scheduled = sum(len(tasks) for tasks in scheduled_tasks.values())
        print(f"  ⏰ 计划任务: {total_scheduled} 个")
    else:
        print("  ⏰ 计划任务: 0 个")
    
    print(f"  🕐 查询时间: {queue_info.get('timestamp', 'Unknown')}")
    
    # === 6. 任务取消演示 ===
    print("\n❌ 6. 任务取消演示")
    print("-" * 30)
    
    # 提交一个长任务然后取消它
    cancel_task_id = handler.submit_long_task(duration=60)
    print(f"✅ 提交待取消任务: {cancel_task_id}")
    
    time.sleep(2)  # 等待任务开始
    
    # 取消任务
    cancel_result = handler.cancel_task(cancel_task_id)
    print(f"🛑 取消任务: {json.dumps(cancel_result, ensure_ascii=False, indent=2)}")
    
    # 检查取消后的状态
    time.sleep(1)
    final_status = handler.get_task_status(cancel_task_id)
    print(f"📋 取消后状态: {final_status.get('state', 'UNKNOWN')}")
    
    print("\n🎉 演示完成!")
    print("=" * 60)

def demo_advanced_features():
    """演示高级功能"""
    print("\n🔧 高级功能演示")
    print("=" * 30)
    
    handler = CeleryHandler()
    
    # 并发任务提交
    print("🚀 并发任务提交演示:")
    task_ids = []
    
    for i in range(5):
        task_id = handler.submit_simple_task(f"并发任务_{i+1}", delay=2)
        task_ids.append(task_id)
        print(f"  ✅ 提交任务 {i+1}: {task_id}")
    
    # 等待所有任务完成
    print("\n⏳ 等待所有并发任务完成...")
    completed_count = 0
    
    while completed_count < len(task_ids):
        completed_count = 0
        for task_id in task_ids:
            status = handler.get_task_status(task_id)
            if status.get('ready'):
                completed_count += 1
        
        print(f"  📊 完成进度: {completed_count}/{len(task_ids)}")
        if completed_count < len(task_ids):
            time.sleep(1)
    
    print("✨ 所有并发任务已完成!")

if __name__ == "__main__":
    print("🎯 CeleryHandler 消息队列演示")
    print("请确保 Redis 服务正在运行，并且已启动 Celery Worker")
    print("启动 Worker 命令: celery -A celery_handler.CeleryHandler.app worker --loglevel=info")
    print()
    
    try:
        # 基础操作演示
        demo_queue_operations()
        
        # 高级功能演示
        demo_advanced_features()
        
    except KeyboardInterrupt:
        print("\n⛔ 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
