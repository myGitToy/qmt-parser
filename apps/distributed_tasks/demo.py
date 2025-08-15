#!/usr/bin/env python3
"""
分布式股票数据处理系统演示脚本
完全模仿akshare的update_sequence_add和update_sequence_launch功能
"""

import sys
import os
import logging
from datetime import datetime, timedelta
import time

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from distributed_tasks.task_manager import DistributedTaskManager
from distributed_tasks.config import get_config
from distributed_tasks.redis_manager import RedisTaskManager
from distributed_tasks.mysql_connector import MySQLConnector

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('demo_distributed_tasks.log')
        ]
    )

def check_prerequisites():
    """检查先决条件"""
    print("=== 检查系统先决条件 ===")
    
    # 获取配置
    config = get_config()
    
    issues = []
    
    # 检查Redis连接
    try:
        redis_manager = RedisTaskManager()
        redis_health = redis_manager.health_check()
        if redis_health['status'] == 'healthy':
            print("✓ Redis连接正常")
        else:
            issues.append(f"Redis连接失败: {redis_health}")
    except Exception as e:
        issues.append(f"Redis连接错误: {e}")
    
    # 检查MySQL连接
    try:
        mysql_config = config.get_mysql_config()
        with MySQLConnector(mysql_config) as db:
            mysql_health = db.health_check()
            if mysql_health['status'] == 'healthy':
                print("✓ MySQL连接正常")
            else:
                issues.append(f"MySQL连接失败: {mysql_health}")
    except Exception as e:
        issues.append(f"MySQL连接错误: {e}")
    
    # 检查配置
    config_validation = config.validate_config()
    if config_validation['valid']:
        print("✓ 配置验证通过")
    else:
        issues.extend(config_validation['issues'])
    
    if issues:
        print("\n⚠️ 发现以下问题:")
        for issue in issues:
            print(f"  - {issue}")
        print("\n请解决这些问题后再运行演示")
        return False
    
    print("✓ 所有先决条件检查通过")
    return True

def demo_basic_functionality():
    """演示基本功能"""
    print("\n=== 演示基本功能 ===")
    
    # 创建分布式任务管理器
    manager = DistributedTaskManager()
    
    # 1. 获取系统状态
    print("\n1. 获取系统初始状态")
    status = manager.get_comprehensive_status()
    print(f"   系统状态: {status['system_status']}")
    print(f"   Redis健康: {status['redis']['health']['status']}")
    print(f"   MySQL健康: {status['mysql']['health']['status']}")
    
    # 2. 清理系统（确保干净的演示环境）
    print("\n2. 清理系统")
    cleanup_result = manager.cleanup_system()
    print(f"   清理结果: {cleanup_result['status']}")
    if cleanup_result['status'] == 'success':
        print(f"   删除的Redis键: {cleanup_result['redis_cleanup']['keys_deleted']}")
    
    # 3. 添加测试任务序列
    print("\n3. 添加测试任务序列")
    test_codes = ['000001', '000002']  # 使用少量代码进行演示
    start_date = datetime.now() - timedelta(days=2)
    end_date = datetime.now()
    
    add_result = manager.update_sequence_add(
        code_list=test_codes,
        myclass='stock',
        ktype='1m',
        priority=1,
        start_date=start_date,
        end_date=end_date,
        auto_select=False
    )
    
    print(f"   添加结果: {add_result['status']}")
    if add_result['status'] == 'success':
        print(f"   添加任务数: {add_result['tasks_added']}")
        print(f"   证券代码数: {add_result['codes_count']}")
    
    # 4. 查看队列状态
    print("\n4. 查看队列状态")
    queue_stats = manager.redis_manager.get_task_statistics()
    print(f"   高优先级队列长度: {queue_stats['queue_lengths'].get('priority_1', 0)}")
    print(f"   普通优先级队列长度: {queue_stats['queue_lengths'].get('priority_0', 0)}")
    
    return manager

def demo_task_processing(manager):
    """演示任务处理"""
    print("\n=== 演示任务处理 ===")
    
    # 处理少量任务进行演示
    print("\n1. 开始处理任务（直接模式）")
    print("   注意: 使用直接处理模式，不依赖Celery")
    
    try:
        launch_result = manager.update_sequence_launch(
            priority=1,
            sleep=0.1,  # 演示用较短间隔
            max_tasks=2,  # 只处理2个任务
            use_celery=False  # 使用直接处理模式
        )
        
        print(f"   处理结果: {launch_result['status']}")
        if launch_result['status'] == 'completed':
            print(f"   处理任务数: {launch_result['tasks_processed']}")
            print(f"   成功任务数: {launch_result['tasks_succeeded']}")
            print(f"   失败任务数: {launch_result['tasks_failed']}")
            print(f"   成功率: {launch_result['success_rate']:.1f}%")
            print(f"   持续时间: {launch_result['duration_seconds']:.2f}秒")
        
    except KeyboardInterrupt:
        print("   用户中断任务处理")
    except Exception as e:
        print(f"   处理出错: {e}")

def demo_akshare_simulation(manager):
    """演示akshare工作流模拟"""
    print("\n=== 演示akshare工作流模拟 ===")
    
    print("\n原始akshare代码:")
    print("```python")
    print("a = data()")
    print("a.start_date = datetime(2024, 6, 20)")
    print("a.end_date = datetime.now()")
    print("a.update_sequence_launch(priority=1, sleep=0.05)")
    print("a.update_sequence_launch(priority=0, sleep=1.5)")
    print("```")
    
    print("\n对应的分布式系统代码:")
    print("```python")
    print("manager = DistributedTaskManager()")
    print("manager.update_sequence_add(myclass='stock', ktype='1m', priority=1)")
    print("manager.update_sequence_launch(priority=1, sleep=0.05)")
    print("manager.update_sequence_launch(priority=0, sleep=1.5)")
    print("```")
    
    # 实际运行模拟
    print("\n执行模拟工作流...")
    try:
        simulation_result = manager.simulate_akshare_workflow()
        print(f"模拟结果: {simulation_result['status']}")
        
        if simulation_result['status'] == 'completed':
            steps = simulation_result['steps']
            print("执行步骤:")
            for step_name, step_result in steps.items():
                print(f"  {step_name}: {step_result.get('status', 'unknown')}")
    except Exception as e:
        print(f"模拟执行出错: {e}")

def demo_monitoring_and_stats(manager):
    """演示监控和统计功能"""
    print("\n=== 演示监控和统计功能 ===")
    
    # 获取综合状态
    print("\n1. 综合系统状态")
    comprehensive_status = manager.get_comprehensive_status()
    
    print(f"   系统整体状态: {comprehensive_status['system_status']}")
    
    # Redis统计
    redis_stats = comprehensive_status['redis']['statistics']
    print(f"   Redis队列统计:")
    for queue, length in redis_stats['queue_lengths'].items():
        print(f"     {queue}: {length} 个任务")
    
    # MySQL表信息
    mysql_tables = comprehensive_status['mysql']['table_info']
    print(f"   MySQL表信息:")
    for table, info in mysql_tables.items():
        if 'error' not in info:
            print(f"     {table}: {info.get('total_rows', 0)} 行数据")
        else:
            print(f"     {table}: {info['error']}")
    
    # 消费者统计
    consumer_stats = comprehensive_status['consumer']
    print(f"   消费者统计:")
    print(f"     处理任务总数: {consumer_stats['tasks_processed']}")
    print(f"     成功任务数: {consumer_stats['tasks_succeeded']}")
    print(f"     失败任务数: {consumer_stats['tasks_failed']}")

def demo_cleanup_and_maintenance(manager):
    """演示清理和维护功能"""
    print("\n=== 演示清理和维护功能 ===")
    
    # 清理系统
    print("\n1. 系统清理")
    cleanup_result = manager.cleanup_system()
    print(f"   清理状态: {cleanup_result['status']}")
    
    # 清理过期任务
    print("\n2. 清理过期任务")
    expired_count = manager.redis_manager.clear_completed_tasks(older_than_hours=0.01)
    print(f"   清理过期任务数: {expired_count}")

def print_system_architecture():
    """打印系统架构图"""
    print("\n=== 系统架构 ===")
    print("""
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │   Task Producer │    │   Redis Queue   │    │  Task Consumer  │
    │    (生产者)      │───▶│    (任务队列)    │───▶│    (消费者)      │
    └─────────────────┘    └─────────────────┘    └─────────────────┘
             │                       │                       │
             │              ┌─────────────────┐              │
             │              │  Celery Tasks   │              │
             │              │   (分布式任务)   │              │
             │              └─────────────────┘              │
             │                       │                       │
             ▼                       ▼                       ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                        MySQL Database                          │
    │                        (最终数据存储)                           │
    └─────────────────────────────────────────────────────────────────┘
    """)

def print_usage_instructions():
    """打印使用说明"""
    print("\n=== 使用说明 ===")
    print("""
1. 启动Redis服务器:
   redis-server

2. 启动Celery Worker (可选，用于分布式处理):
   celery -A distributed_tasks.celery_tasks worker --loglevel=info

3. 启动Celery监控 (可选):
   celery -A distributed_tasks.celery_tasks flower

4. 使用Python代码:
   from distributed_tasks.task_manager import DistributedTaskManager
   manager = DistributedTaskManager()
   
   # 添加任务
   manager.update_sequence_add(myclass='stock', ktype='1m', priority=1)
   
   # 处理任务
   manager.update_sequence_launch(priority=1, sleep=0.05)
    """)

def main():
    """主函数"""
    print("🚀 分布式股票数据处理系统演示")
    print("=" * 50)
    
    # 设置日志
    setup_logging()
    
    # 打印系统架构
    print_system_architecture()
    
    # 检查先决条件
    if not check_prerequisites():
        print("\n❌ 先决条件检查失败，退出演示")
        return
    
    try:
        # 演示基本功能
        manager = demo_basic_functionality()
        
        # 演示任务处理
        demo_task_processing(manager)
        
        # 演示akshare工作流模拟
        demo_akshare_simulation(manager)
        
        # 演示监控和统计
        demo_monitoring_and_stats(manager)
        
        # 演示清理和维护
        demo_cleanup_and_maintenance(manager)
        
        print("\n✅ 演示完成!")
        
        # 打印使用说明
        print_usage_instructions()
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断演示")
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        logging.exception("演示失败")
    
    print("\n📝 详细日志已保存到: demo_distributed_tasks.log")

if __name__ == "__main__":
    main()
