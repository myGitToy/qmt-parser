"""
分布式任务管理器
整合生产者和消费者，提供统一的管理接口
模仿akshare的完整数据更新流程
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# 添加当前目录到Python路径，解决相对导入问题
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 添加父目录到Python路径
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    # 尝试相对导入
    from .task_producer import TaskProducer
    from .task_consumer import TaskConsumer
    from .redis_manager import RedisTaskManager
    from .mysql_connector import MySQLConnector
except ImportError:
    # 如果相对导入失败，使用绝对导入
    try:
        from task_producer import TaskProducer
        from task_consumer import TaskConsumer
        from redis_manager import RedisTaskManager
        from mysql_connector import MySQLConnector
    except ImportError:
        # 最后尝试完整路径导入
        from distributed_tasks.task_producer import TaskProducer
        from distributed_tasks.task_consumer import TaskConsumer
        from distributed_tasks.redis_manager import RedisTaskManager
        from distributed_tasks.mysql_connector import MySQLConnector

class DistributedTaskManager:
    """分布式任务管理器"""
    
    def __init__(self, 
                 redis_config: Optional[Dict] = None,
                 mysql_config: Optional[Dict] = None):
        """
        初始化分布式任务管理器
        
        Args:
            redis_config: Redis配置字典
            mysql_config: MySQL配置字典
        """
        self.logger = logging.getLogger(__name__)
        
        # 初始化各组件
        self.redis_config = redis_config
        self.mysql_config = mysql_config
        
        self.producer = TaskProducer(redis_config)
        self.consumer = TaskConsumer(redis_config, mysql_config)
        self.redis_manager = RedisTaskManager(**(redis_config or {}))
        
        self.logger.info("分布式任务管理器初始化完成")
    
    def update_sequence_add(self, 
                           code_list: Optional[List[str]] = None,
                           myclass: str = 'stock',
                           ktype: str = '60m',
                           priority: int = 0,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           auto_select: bool = True) -> Dict[str, Any]:
        """
        添加更新序列（完全模仿akshare的update_sequence_add）
        
        Args:
            code_list: 证券代码列表
            myclass: 证券类别 ('stock', 'etf')
            ktype: K线类型 ('1m', '5m', '60m', '1d')
            priority: 优先级 (0=普通, 1=高优先级)
            start_date: 开始日期
            end_date: 结束日期
            auto_select: 是否自动选择证券代码
            
        Returns:
            操作结果字典
        """
        self.logger.info(f"添加更新序列: {myclass}-{ktype}, 优先级: {priority}")
        
        return self.producer.add_update_sequence(
            code_list=code_list,
            myclass=myclass,
            ktype=ktype,
            priority=priority,
            start_date=start_date,
            end_date=end_date,
            auto_select=auto_select
        )
    
    def update_sequence_launch(self, 
                              priority: int = 0,
                              sleep: float = 0.05,
                              max_tasks: Optional[int] = None,
                              use_celery: bool = True) -> Dict[str, Any]:
        """
        启动序列更新（完全模仿akshare的update_sequence_launch）
        
        Args:
            priority: 处理的任务优先级
            sleep: 任务间隔时间
            max_tasks: 最大处理任务数
            use_celery: 是否使用Celery分布式处理
            
        Returns:
            执行结果字典
        """
        self.logger.info(f"启动序列更新: 优先级 {priority}, 间隔 {sleep}s")
        
        # 设置消费者的休眠间隔
        self.consumer.sleep_interval = sleep
        
        return self.consumer.start_consumer(
            priority=priority,
            max_tasks=max_tasks,
            use_celery=use_celery
        )
    
    def run_complete_update_cycle(self, 
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None,
                                 sleep_between_priorities: float = 1.0) -> Dict[str, Any]:
        """
        运行完整的更新周期（模仿实际使用场景）
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            sleep_between_priorities: 不同优先级之间的间隔时间
            
        Returns:
            完整周期的执行结果
        """
        cycle_start_time = datetime.now()
        self.logger.info("开始完整的数据更新周期")
        
        try:
            # 1. 创建标准更新序列
            self.logger.info("步骤1: 创建标准更新序列")
            sequence_result = self.producer.create_standard_sequences(
                start_date=start_date,
                end_date=end_date
            )
            
            if sequence_result['status'] != 'completed':
                return {
                    'status': 'failed',
                    'step': 'create_sequences',
                    'error': 'Failed to create sequences',
                    'details': sequence_result
                }
            
            # 2. 处理高优先级任务
            self.logger.info("步骤2: 处理高优先级任务")
            high_priority_result = self.update_sequence_launch(
                priority=1,
                sleep=0.05,
                use_celery=True
            )
            
            # 间隔时间
            import time
            time.sleep(sleep_between_priorities)
            
            # 3. 处理普通优先级任务  
            self.logger.info("步骤3: 处理普通优先级任务")
            normal_priority_result = self.update_sequence_launch(
                priority=0,
                sleep=1.5,
                use_celery=True
            )
            
            # 4. 生成总结报告
            cycle_end_time = datetime.now()
            cycle_duration = (cycle_end_time - cycle_start_time).total_seconds()
            
            final_stats = self.get_comprehensive_status()
            
            cycle_result = {
                'status': 'completed',
                'cycle_start_time': cycle_start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'cycle_end_time': cycle_end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'cycle_duration_seconds': cycle_duration,
                'sequence_creation': sequence_result,
                'high_priority_execution': high_priority_result,
                'normal_priority_execution': normal_priority_result,
                'final_statistics': final_stats
            }
            
            self.logger.info(f"完整更新周期完成，耗时 {cycle_duration:.2f} 秒")
            return cycle_result
            
        except Exception as e:
            error_msg = f"完整更新周期失败: {str(e)}"
            self.logger.error(error_msg)
            return {
                'status': 'failed',
                'error': error_msg,
                'cycle_start_time': cycle_start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'failure_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """
        获取系统综合状态
        
        Returns:
            综合状态信息
        """
        try:
            # Redis状态
            redis_stats = self.redis_manager.get_task_statistics()
            redis_health = self.redis_manager.health_check()
            
            # MySQL状态
            mysql_health = None
            table_info = {}
            
            try:
                with MySQLConnector(self.mysql_config) as db:
                    mysql_health = db.health_check()
                    
                    # 获取各表信息
                    for ktype in ['1m', '5m', '60m', '1d']:
                        try:
                            table_info[ktype] = db.get_table_info(ktype)
                        except:
                            table_info[ktype] = {'error': 'Table not found or inaccessible'}
            except Exception as e:
                mysql_health = {'status': 'unhealthy', 'error': str(e)}
            
            # 消费者统计
            consumer_stats = self.consumer.get_stats()
            
            return {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'redis': {
                    'statistics': redis_stats,
                    'health': redis_health
                },
                'mysql': {
                    'health': mysql_health,
                    'table_info': table_info
                },
                'consumer': consumer_stats,
                'system_status': 'healthy' if (
                    redis_health.get('status') == 'healthy' and 
                    mysql_health and mysql_health.get('status') == 'healthy'
                ) else 'degraded'
            }
            
        except Exception as e:
            return {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'system_status': 'error',
                'error': str(e)
            }
    
    def cleanup_system(self) -> Dict[str, Any]:
        """
        清理系统（清空队列、清理过期任务等）
        
        Returns:
            清理结果
        """
        try:
            self.logger.info("开始系统清理")
            
            # 清理Redis队列和任务
            redis_cleanup = self.producer.clear_all_sequences()
            
            # 清理过期任务记录
            expired_cleanup = self.redis_manager.clear_completed_tasks(older_than_hours=1)
            
            return {
                'status': 'success',
                'redis_cleanup': redis_cleanup,
                'expired_tasks_deleted': expired_cleanup,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def emergency_stop(self) -> Dict[str, Any]:
        """
        紧急停止所有任务
        
        Returns:
            停止结果
        """
        try:
            self.logger.warning("执行紧急停止")
            
            # 停止消费者
            self.consumer.stop()
            
            # 可以在这里添加停止Celery worker的逻辑
            # 例如通过Redis发送停止信号
            
            return {
                'status': 'success',
                'message': 'Emergency stop executed',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def simulate_akshare_workflow(self) -> Dict[str, Any]:
        """
        模拟原始akshare工作流程
        
        Returns:
            模拟结果
        """
        self.logger.info("开始模拟akshare工作流程")
        
        # 设置时间范围
        start_date = datetime(2024, 6, 20)
        end_date = datetime.now()
        
        try:
            # 步骤1: 添加高优先级股票1分钟线任务
            result1 = self.update_sequence_add(
                myclass='stock',
                ktype='1m', 
                priority=1,
                start_date=start_date,
                end_date=end_date
            )
            
            # 步骤2: 添加普通优先级股票60分钟线任务
            result2 = self.update_sequence_add(
                myclass='stock',
                ktype='60m',
                priority=0,
                start_date=start_date,
                end_date=end_date
            )
            
            # 步骤3: 执行高优先级任务
            launch1 = self.update_sequence_launch(
                priority=1,
                sleep=0.05
            )
            
            # 步骤4: 执行普通优先级任务
            launch2 = self.update_sequence_launch(
                priority=0,
                sleep=1.5
            )
            
            return {
                'status': 'completed',
                'steps': {
                    'add_high_priority': result1,
                    'add_normal_priority': result2,
                    'launch_high_priority': launch1,
                    'launch_normal_priority': launch2
                },
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

if __name__ == "__main__":
    # 测试和演示代码
    logging.basicConfig(level=logging.INFO)
    
    # 创建分布式任务管理器
    manager = DistributedTaskManager()
    
    print("=== 分布式任务管理器演示 ===")
    
    # 1. 获取系统状态
    print("\n1. 获取系统状态")
    status = manager.get_comprehensive_status()
    print(f"系统状态: {status['system_status']}")
    
    # 2. 清理系统
    print("\n2. 清理系统")
    cleanup_result = manager.cleanup_system()
    print(f"清理结果: {cleanup_result['status']}")
    
    # 3. 添加测试任务序列
    print("\n3. 添加测试任务序列")
    add_result = manager.update_sequence_add(
        code_list=['000001', '000002'],
        myclass='stock',
        ktype='1m',
        priority=1,
        start_date=datetime.now() - timedelta(days=1),
        end_date=datetime.now(),
        auto_select=False
    )
    print(f"任务添加结果: {add_result['status']}")
    
    # 4. 处理任务（少量测试）
    print("\n4. 处理任务")
    try:
        launch_result = manager.update_sequence_launch(
            priority=1,
            sleep=0.1,
            max_tasks=2,  # 只处理2个任务用于测试
            use_celery=False  # 使用直接处理模式
        )
        print(f"任务处理结果: {launch_result['status']}")
    except KeyboardInterrupt:
        print("用户中断任务处理")
    
    # 5. 最终状态
    print("\n5. 最终系统状态")
    final_status = manager.get_comprehensive_status()
    print(f"最终状态: {final_status['system_status']}")
    
    print("\n=== 演示完成 ===")
