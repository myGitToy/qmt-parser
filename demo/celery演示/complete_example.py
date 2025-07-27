"""
完整的 Celery 证券数据更新系统使用示例
展示如何使用环境变量配置和完整的工作流程
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from demo_celery import (
    app, 
    update_single_security,
    batch_update_securities,
    SecurityDataUpdater
)

from usage_example import SecurityTaskManager

def setup_environment():
    """设置环境"""
    print("=== 环境设置 ===")
    
    # 加载环境变量
    load_dotenv()
    
    # 显示配置信息
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = os.getenv('REDIS_PORT', '6379')
    redis_password = os.getenv('REDIS_PASSWORD', '')
    
    print(f"Redis 配置:")
    print(f"  主机: {redis_host}")
    print(f"  端口: {redis_port}")
    print(f"  密码: {'已设置' if redis_password else '未设置'}")
    
    # 测试Redis连接
    try:
        from test_redis_connection import test_redis_connection
        if test_redis_connection():
            print("✓ Redis 连接测试成功")
        else:
            print("❌ Redis 连接测试失败")
            return False
    except ImportError:
        print("⚠️  无法导入Redis测试模块")
    
    return True

def demo_complete_workflow():
    """完整工作流程演示"""
    print("\n=== 完整工作流程演示 ===")
    
    # 1. 初始化任务管理器
    manager = SecurityTaskManager()
    
    # 2. 提交单个证券更新任务
    print("\n1. 提交单个证券更新任务...")
    single_task_id = manager.submit_single_update('000001', '平安银行', 'price')
    print(f"   任务ID: {single_task_id}")
    
    # 3. 提交批量更新任务
    print("\n2. 提交批量更新任务...")
    batch_task_id = manager.submit_batch_update(3)
    print(f"   批量任务ID: {batch_task_id}")
    
    # 4. 监控任务状态
    print("\n3. 监控任务状态...")
    for i in range(10):  # 监控10次
        print(f"   检查第 {i+1} 次...")
        
        # 检查单个任务状态
        single_status = manager.check_task_status(single_task_id)
        print(f"   单个任务状态: {single_status.get('status', 'UNKNOWN')}")
        
        # 检查批量任务状态
        batch_status = manager.check_task_status(batch_task_id)
        print(f"   批量任务状态: {batch_status.get('status', 'UNKNOWN')}")
        
        # 如果任务完成，退出监控
        if (single_status.get('ready', False) and 
            batch_status.get('ready', False)):
            print("   所有任务已完成！")
            break
        
        time.sleep(5)  # 等待5秒
    
    # 5. 查看最终结果
    print("\n4. 查看最终结果...")
    final_single_status = manager.check_task_status(single_task_id)
    final_batch_status = manager.check_task_status(batch_task_id)
    
    print(f"   单个任务最终状态: {final_single_status}")
    print(f"   批量任务最终状态: {final_batch_status}")
    
    # 6. 查看活跃任务和队列状态
    print("\n5. 查看系统状态...")
    active_tasks = manager.get_active_tasks()
    queue_length = manager.get_queue_length()
    
    print(f"   活跃任务数: {len(active_tasks) if active_tasks else 0}")
    print(f"   队列长度: {queue_length}")

def demo_database_operations():
    """数据库操作演示"""
    print("\n=== 数据库操作演示 ===")
    
    try:
        # 创建数据更新器
        updater = SecurityDataUpdater()
        
        # 获取待更新任务
        print("1. 获取待更新任务...")
        pending_tasks = updater.get_pending_updates()
        print(f"   找到 {len(pending_tasks)} 个待更新任务")
        
        # 显示前几个任务
        for i, task in enumerate(pending_tasks[:3]):
            print(f"   任务 {i+1}: {task['security_code']} - {task['security_name']}")
        
        # 如果没有待更新任务，可以手动插入一些示例数据
        if not pending_tasks:
            print("   没有待更新任务，建议运行以下SQL创建示例数据：")
            print("""
            INSERT INTO securities_update_queue (security_code, security_name, update_type, priority) VALUES
            ('000001', '平安银行', 'all', 1),
            ('000002', '万科A', 'price', 2),
            ('600519', '贵州茅台', 'all', 3);
            """)
        
    except Exception as e:
        print(f"   数据库操作失败: {e}")
        print("   请确保数据库连接配置正确，并且已创建相应的表")

def show_usage_instructions():
    """显示使用说明"""
    print("\n=== 使用说明 ===")
    print("1. 确保Redis服务正在运行")
    print("2. 确保MySQL数据库可访问")
    print("3. 启动Celery Worker:")
    print("   python start_celery.py worker")
    print("4. 启动Flower监控界面（可选）:")
    print("   python start_celery.py flower")
    print("5. 运行此脚本进行测试:")
    print("   python complete_example.py")

def main():
    """主函数"""
    print("=== Celery 证券数据更新系统 - 完整示例 ===")
    
    try:
        # 1. 设置环境
        if not setup_environment():
            print("❌ 环境设置失败，请检查配置")
            return
        
        # 2. 显示使用说明
        show_usage_instructions()
        
        # 3. 数据库操作演示
        demo_database_operations()
        
        # 4. 询问是否继续演示工作流程
        response = input("\n是否继续演示完整工作流程？(y/n): ")
        if response.lower() == 'y':
            demo_complete_workflow()
        else:
            print("演示结束。")
        
    except KeyboardInterrupt:
        print("\n\n演示被用户中断。")
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
