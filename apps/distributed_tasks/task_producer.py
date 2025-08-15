"""
任务队列生产者
用于创建和管理股票数据更新任务
模仿akshare的update_sequence_add功能
"""

import sys
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

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
    from .redis_manager import RedisTaskManager
    from .celery_tasks import batch_process_codes
except ImportError:
    # 如果相对导入失败，使用绝对导入
    try:
        from redis_manager import RedisTaskManager
        from celery_tasks import batch_process_codes
    except ImportError:
        # 最后尝试完整路径导入
        from distributed_tasks.redis_manager import RedisTaskManager
        from distributed_tasks.celery_tasks import batch_process_codes

try:
    from apt.vendor.tspro.security import security
except ImportError:
    # 如果无法导入security模块，设置为None
    security = None

class TaskProducer:
    """任务生产者类"""
    
    def __init__(self, redis_config: Optional[Dict] = None):
        """
        初始化任务生产者
        
        Args:
            redis_config: Redis配置字典
        """
        self.logger = logging.getLogger(__name__)
        
        # 初始化Redis管理器
        if redis_config:
            self.redis_manager = RedisTaskManager(**redis_config)
        else:
            self.redis_manager = RedisTaskManager()
        
        # 初始化证券管理器
        try:
            if security is not None:
                self.security = security()
            else:
                self.security = None
        except Exception as e:
            self.logger.warning(f"无法初始化security模块: {e}")
            self.security = None
    
    def add_update_sequence(self, 
                           code_list: Optional[List[str]] = None,
                           myclass: str = 'stock',
                           ktype: str = '60m',
                           priority: int = 0,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           auto_select: bool = True) -> Dict[str, Any]:
        """
        添加更新序列（模仿akshare的update_sequence_add）
        
        Args:
            code_list: 证券代码列表，如果为None则自动获取
            myclass: 证券类别 ('stock', 'etf')
            ktype: K线类型 ('1m', '5m', '60m', '1d')
            priority: 优先级 (0=普通, 1=高优先级)
            start_date: 开始日期
            end_date: 结束日期
            auto_select: 是否自动选择证券代码
            
        Returns:
            操作结果字典
        """
        try:
            # 设置默认日期
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            # 自动获取证券代码列表
            if code_list is None and auto_select:
                if self.security:
                    try:
                        if myclass == 'stock':
                            code_df = self.security.get_all_code(day=end_date, type=['stock'])
                        elif myclass == 'etf':
                            code_df = self.security.get_all_code(day=end_date, type=['etf'])
                        else:
                            raise ValueError(f"不支持的证券类别: {myclass}")
                        
                        code_list = code_df['code'].tolist()
                        self.logger.info(f"自动获取了 {len(code_list)} 个 {myclass} 代码")
                        
                    except Exception as e:
                        self.logger.error(f"自动获取证券代码失败: {e}")
                        return {
                            'status': 'failed',
                            'error': f"自动获取证券代码失败: {e}",
                            'tasks_added': 0
                        }
                else:
                    # 使用默认测试代码
                    if myclass == 'stock':
                        code_list = ['000001', '000002', '000858', '600000', '600036']
                    elif myclass == 'etf':
                        code_list = ['510050', '510300', '159919']
                    else:
                        return {
                            'status': 'failed',
                            'error': f"无法获取 {myclass} 的默认代码列表",
                            'tasks_added': 0
                        }
                    
                    self.logger.warning(f"使用默认 {myclass} 代码列表: {code_list}")
            
            elif code_list is None:
                return {
                    'status': 'failed',
                    'error': "必须提供证券代码列表或启用自动选择",
                    'tasks_added': 0
                }
            
            # 添加任务到Redis队列
            task_count = self.redis_manager.add_task_sequence(
                code_list=code_list,
                start_date=start_date,
                end_date=end_date,
                myclass=myclass,
                ktype=ktype,
                priority=priority
            )
            
            result = {
                'status': 'success',
                'tasks_added': task_count,
                'codes_count': len(code_list),
                'myclass': myclass,
                'ktype': ktype,
                'priority': priority,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'message': f"成功添加 {task_count} 个 {myclass}-{ktype} 任务到优先级 {priority} 队列"
            }
            
            self.logger.info(result['message'])
            return result
            
        except Exception as e:
            error_msg = f"添加更新序列失败: {str(e)}"
            self.logger.error(error_msg)
            return {
                'status': 'failed',
                'error': error_msg,
                'tasks_added': 0
            }
    
    def bulk_add_sequences(self, sequences: List[Dict]) -> Dict[str, Any]:
        """
        批量添加多个更新序列
        
        Args:
            sequences: 序列配置列表，每个字典包含序列参数
            
        Returns:
            批量操作结果
        """
        results = []
        total_tasks = 0
        
        for i, seq_config in enumerate(sequences):
            try:
                result = self.add_update_sequence(**seq_config)
                results.append({
                    'sequence_index': i,
                    'config': seq_config,
                    'result': result
                })
                
                if result['status'] == 'success':
                    total_tasks += result['tasks_added']
                    
            except Exception as e:
                results.append({
                    'sequence_index': i,
                    'config': seq_config,
                    'result': {
                        'status': 'failed',
                        'error': str(e),
                        'tasks_added': 0
                    }
                })
        
        return {
            'status': 'completed',
            'total_sequences': len(sequences),
            'total_tasks_added': total_tasks,
            'results': results
        }
    
    def clear_all_sequences(self) -> Dict[str, Any]:
        """
        清理所有更新序列
        
        Returns:
            清理结果
        """
        try:
            # 清理Redis中的所有队列和状态
            patterns_to_clear = [
                f"{self.redis_manager.TASK_QUEUE_PREFIX}:*",
                f"{self.redis_manager.TASK_STATUS_PREFIX}:*", 
                f"{self.redis_manager.SEQUENCE_SET_PREFIX}:*"
            ]
            
            total_deleted = 0
            
            for pattern in patterns_to_clear:
                keys = self.redis_manager.redis_client.keys(pattern)
                if keys:
                    deleted = self.redis_manager.redis_client.delete(*keys)
                    total_deleted += deleted
            
            result = {
                'status': 'success',
                'keys_deleted': total_deleted,
                'message': f"成功清理 {total_deleted} 个Redis键"
            }
            
            self.logger.info(result['message'])
            return result
            
        except Exception as e:
            error_msg = f"清理序列失败: {str(e)}"
            self.logger.error(error_msg)
            return {
                'status': 'failed',
                'error': error_msg,
                'keys_deleted': 0
            }
    
    def get_sequence_status(self) -> Dict[str, Any]:
        """
        获取序列状态统计
        
        Returns:
            状态统计信息
        """
        try:
            stats = self.redis_manager.get_task_statistics()
            
            # 添加更多详细信息
            detailed_stats = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'queue_statistics': stats,
                'redis_health': self.redis_manager.health_check(),
            }
            
            return {
                'status': 'success',
                'statistics': detailed_stats
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def create_standard_sequences(self, 
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        创建标准的更新序列（模仿常用的akshare更新模式）
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            创建结果
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now()
        
        # 定义标准序列配置
        standard_sequences = [
            # 高优先级：股票1分钟线
            {
                'myclass': 'stock',
                'ktype': '1m',
                'priority': 1,
                'start_date': start_date,
                'end_date': end_date,
                'auto_select': True
            },
            # 普通优先级：股票60分钟线
            {
                'myclass': 'stock', 
                'ktype': '60m',
                'priority': 0,
                'start_date': start_date,
                'end_date': end_date,
                'auto_select': True
            },
            # 普通优先级：股票5分钟线
            {
                'myclass': 'stock',
                'ktype': '5m', 
                'priority': 0,
                'start_date': start_date,
                'end_date': end_date,
                'auto_select': True
            },
            # 高优先级：ETF1分钟线
            {
                'myclass': 'etf',
                'ktype': '1m',
                'priority': 1,
                'start_date': start_date,
                'end_date': end_date,
                'auto_select': True
            },
            # 普通优先级：ETF60分钟线
            {
                'myclass': 'etf',
                'ktype': '60m',
                'priority': 0,
                'start_date': start_date,
                'end_date': end_date,
                'auto_select': True
            }
        ]
        
        return self.bulk_add_sequences(standard_sequences)

if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    # 创建任务生产者
    producer = TaskProducer()
    
    # 测试获取序列状态
    status = producer.get_sequence_status()
    print(f"当前序列状态: {status}")
    
    # 测试添加单个序列
    result = producer.add_update_sequence(
        code_list=['000001', '000002'],
        myclass='stock',
        ktype='1m',
        priority=1,
        start_date=datetime.now() - timedelta(days=3),
        end_date=datetime.now(),
        auto_select=False
    )
    print(f"添加序列结果: {result}")
    
    # 测试创建标准序列
    print("创建标准序列...")
    standard_result = producer.create_standard_sequences()
    print(f"标准序列创建结果: {standard_result}")
    
    # 再次查看状态
    final_status = producer.get_sequence_status()
    print(f"最终序列状态: {final_status}")
