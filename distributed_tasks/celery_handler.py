"""
Celery消息队列处理器
演示消息队列的基础操作方法
提供简单易用的任务管理接口
"""

import sys
import os
from typing import Dict, List, Any, Optional, Union
import json
import time
from datetime import datetime, timedelta
import logging
from celery import Celery
from celery.result import AsyncResult
from celery.exceptions import Retry

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入配置
try:
    from .config import get_config
except ImportError:
    try:
        from config import get_config
    except ImportError:
        from distributed_tasks.config import get_config

class CeleryHandler:
    """Celery消息队列处理器类"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化Celery处理器
        
        Args:
            config: 配置字典，包含Redis连接信息
        """
        self.logger = logging.getLogger(__name__)
        
        # 获取配置
        if config is None:
            config = get_config()
        
        self.config = config
        
        # 创建Celery应用实例
        self.app = Celery('celery_handler_demo')
        
        # 配置Celery
        self._configure_celery()
        
        # 注册基础任务
        self._register_tasks()
    
    def _configure_celery(self):
        """配置Celery"""
        redis_config = self.config.get('redis', {})
        redis_url = f"redis://{redis_config.get('host', 'localhost')}:{redis_config.get('port', 6379)}"
        
        self.app.conf.update(
            # 使用Redis作为消息代理和结果后端
            broker_url=f"{redis_url}/{redis_config.get('broker_db', 1)}",
            result_backend=f"{redis_url}/{redis_config.get('result_db', 2)}",
            
            # 任务序列化
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='Asia/Shanghai',
            enable_utc=True,
            
            # 任务路由
            task_routes={
                'celery_handler_demo.simple_task': {'queue': 'default'},
                'celery_handler_demo.long_running_task': {'queue': 'long_tasks'},
                'celery_handler_demo.batch_task': {'queue': 'batch'},
                'celery_handler_demo.error_task': {'queue': 'default'},
            },
            
            # 工作进程配置
            worker_prefetch_multiplier=1,
            task_acks_late=True,
            
            # 结果过期时间
            result_expires=3600,
        )
    
    def _register_tasks(self):
        """注册演示任务"""
        
        @self.app.task(name='celery_handler_demo.simple_task', bind=True)
        def simple_task(self, message: str, delay: int = 1) -> Dict:
            """简单任务示例"""
            try:
                self.logger.info(f"开始执行简单任务: {message}")
                time.sleep(delay)
                
                result = {
                    'task_id': self.request.id,
                    'message': message,
                    'delay': delay,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'completed'
                }
                
                self.logger.info(f"简单任务完成: {result}")
                return result
                
            except Exception as e:
                self.logger.error(f"简单任务失败: {e}")
                raise
        
        @self.app.task(name='celery_handler_demo.long_running_task', bind=True)
        def long_running_task(self, duration: int = 30, progress_updates: bool = True) -> Dict:
            """长时间运行任务示例"""
            try:
                self.logger.info(f"开始执行长时间任务，预计耗时: {duration}秒")
                
                for i in range(duration):
                    time.sleep(1)
                    
                    if progress_updates and i % 5 == 0:
                        # 更新任务进度
                        progress = int((i + 1) / duration * 100)
                        self.update_state(
                            state='PROGRESS',
                            meta={
                                'current': i + 1,
                                'total': duration,
                                'percentage': progress,
                                'message': f'进度: {progress}%'
                            }
                        )
                        self.logger.info(f"任务进度: {progress}%")
                
                result = {
                    'task_id': self.request.id,
                    'duration': duration,
                    'completed_at': datetime.now().isoformat(),
                    'status': 'completed'
                }
                
                self.logger.info(f"长时间任务完成: {result}")
                return result
                
            except Exception as e:
                self.logger.error(f"长时间任务失败: {e}")
                raise
        
        @self.app.task(name='celery_handler_demo.batch_task', bind=True)
        def batch_task(self, items: List[str], batch_size: int = 5) -> Dict:
            """批量处理任务示例"""
            try:
                self.logger.info(f"开始批量处理 {len(items)} 个项目")
                
                results = []
                total_batches = (len(items) + batch_size - 1) // batch_size
                
                for batch_idx in range(0, len(items), batch_size):
                    batch_items = items[batch_idx:batch_idx + batch_size]
                    batch_num = batch_idx // batch_size + 1
                    
                    # 处理当前批次
                    batch_results = []
                    for item in batch_items:
                        # 模拟处理每个项目
                        time.sleep(0.5)
                        batch_results.append({
                            'item': item,
                            'processed_at': datetime.now().isoformat(),
                            'status': 'processed'
                        })
                    
                    results.extend(batch_results)
                    
                    # 更新进度
                    progress = int(batch_num / total_batches * 100)
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'current_batch': batch_num,
                            'total_batches': total_batches,
                            'processed_items': len(results),
                            'total_items': len(items),
                            'percentage': progress,
                            'message': f'批次 {batch_num}/{total_batches} 完成'
                        }
                    )
                    
                    self.logger.info(f"批次 {batch_num}/{total_batches} 完成")
                
                final_result = {
                    'task_id': self.request.id,
                    'total_items': len(items),
                    'processed_items': len(results),
                    'batch_size': batch_size,
                    'results': results,
                    'completed_at': datetime.now().isoformat(),
                    'status': 'completed'
                }
                
                self.logger.info(f"批量任务完成: 处理了 {len(results)} 个项目")
                return final_result
                
            except Exception as e:
                self.logger.error(f"批量任务失败: {e}")
                raise
        
        @self.app.task(name='celery_handler_demo.error_task', bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 5})
        def error_task(self, should_fail: bool = True, error_message: str = "模拟错误") -> Dict:
            """错误处理和重试示例"""
            try:
                retry_count = self.request.retries
                self.logger.info(f"执行错误任务 (重试次数: {retry_count})")
                
                if should_fail and retry_count < 2:
                    # 前两次故意失败
                    raise Exception(f"{error_message} (重试 {retry_count + 1})")
                
                result = {
                    'task_id': self.request.id,
                    'retry_count': retry_count,
                    'should_fail': should_fail,
                    'completed_at': datetime.now().isoformat(),
                    'status': 'completed'
                }
                
                self.logger.info(f"错误任务最终成功: {result}")
                return result
                
            except Exception as e:
                self.logger.error(f"错误任务失败 (重试 {self.request.retries + 1}): {e}")
                raise
        
        # 保存任务引用
        self.simple_task = simple_task
        self.long_running_task = long_running_task
        self.batch_task = batch_task
        self.error_task = error_task
    
    # === 基础队列操作方法 ===
    
    def submit_simple_task(self, message: str, delay: int = 1, queue: str = 'default') -> str:
        """
        提交简单任务
        
        Args:
            message: 任务消息
            delay: 延迟秒数
            queue: 队列名称
            
        Returns:
            任务ID
        """
        try:
            result = self.simple_task.apply_async(
                args=[message, delay],
                queue=queue
            )
            
            self.logger.info(f"提交简单任务成功: {result.id}")
            return result.id
            
        except Exception as e:
            self.logger.error(f"提交简单任务失败: {e}")
            raise
    
    def submit_long_task(self, duration: int = 30, progress_updates: bool = True, queue: str = 'long_tasks') -> str:
        """
        提交长时间运行任务
        
        Args:
            duration: 持续时间(秒)
            progress_updates: 是否发送进度更新
            queue: 队列名称
            
        Returns:
            任务ID
        """
        try:
            result = self.long_running_task.apply_async(
                args=[duration, progress_updates],
                queue=queue
            )
            
            self.logger.info(f"提交长时间任务成功: {result.id}")
            return result.id
            
        except Exception as e:
            self.logger.error(f"提交长时间任务失败: {e}")
            raise
    
    def submit_batch_task(self, items: List[str], batch_size: int = 5, queue: str = 'batch') -> str:
        """
        提交批量处理任务
        
        Args:
            items: 要处理的项目列表
            batch_size: 批次大小
            queue: 队列名称
            
        Returns:
            任务ID
        """
        try:
            result = self.batch_task.apply_async(
                args=[items, batch_size],
                queue=queue
            )
            
            self.logger.info(f"提交批量任务成功: {result.id}, 项目数: {len(items)}")
            return result.id
            
        except Exception as e:
            self.logger.error(f"提交批量任务失败: {e}")
            raise
    
    def submit_error_task(self, should_fail: bool = True, error_message: str = "模拟错误", queue: str = 'default') -> str:
        """
        提交错误处理任务（演示重试机制）
        
        Args:
            should_fail: 是否应该失败
            error_message: 错误消息
            queue: 队列名称
            
        Returns:
            任务ID
        """
        try:
            result = self.error_task.apply_async(
                args=[should_fail, error_message],
                queue=queue
            )
            
            self.logger.info(f"提交错误任务成功: {result.id}")
            return result.id
            
        except Exception as e:
            self.logger.error(f"提交错误任务失败: {e}")
            raise
    
    def get_task_status(self, task_id: str) -> Dict:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息
        """
        try:
            result = AsyncResult(task_id, app=self.app)
            
            status_info = {
                'task_id': task_id,
                'state': result.state,
                'ready': result.ready(),
                'successful': result.successful() if result.ready() else None,
                'failed': result.failed() if result.ready() else None,
            }
            
            if result.state == 'PROGRESS':
                status_info['progress'] = result.info
            elif result.ready():
                if result.successful():
                    status_info['result'] = result.result
                else:
                    status_info['error'] = str(result.info)
            
            return status_info
            
        except Exception as e:
            self.logger.error(f"获取任务状态失败: {e}")
            return {
                'task_id': task_id,
                'state': 'UNKNOWN',
                'error': str(e)
            }
    
    def wait_for_task(self, task_id: str, timeout: int = 300, poll_interval: int = 1) -> Dict:
        """
        等待任务完成
        
        Args:
            task_id: 任务ID
            timeout: 超时时间(秒)
            poll_interval: 轮询间隔(秒)
            
        Returns:
            任务结果
        """
        try:
            result = AsyncResult(task_id, app=self.app)
            
            start_time = time.time()
            while not result.ready():
                if time.time() - start_time > timeout:
                    return {
                        'task_id': task_id,
                        'status': 'timeout',
                        'error': f'任务超时 ({timeout}秒)'
                    }
                
                # 显示进度信息
                if result.state == 'PROGRESS':
                    progress_info = result.info
                    self.logger.info(f"任务 {task_id} 进度: {progress_info.get('message', '进行中...')}")
                
                time.sleep(poll_interval)
            
            if result.successful():
                return {
                    'task_id': task_id,
                    'status': 'success',
                    'result': result.result
                }
            else:
                return {
                    'task_id': task_id,
                    'status': 'failed',
                    'error': str(result.info)
                }
                
        except Exception as e:
            self.logger.error(f"等待任务失败: {e}")
            return {
                'task_id': task_id,
                'status': 'error',
                'error': str(e)
            }
    
    def cancel_task(self, task_id: str, terminate: bool = False) -> Dict:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            terminate: 是否强制终止
            
        Returns:
            取消结果
        """
        try:
            result = AsyncResult(task_id, app=self.app)
            
            if terminate:
                self.app.control.terminate(task_id)
                action = 'terminated'
            else:
                self.app.control.revoke(task_id, terminate=False)
                action = 'revoked'
            
            return {
                'task_id': task_id,
                'action': action,
                'status': 'success',
                'message': f'任务已{action}'
            }
            
        except Exception as e:
            self.logger.error(f"取消任务失败: {e}")
            return {
                'task_id': task_id,
                'action': 'cancel',
                'status': 'failed',
                'error': str(e)
            }
    
    def get_queue_info(self) -> Dict:
        """
        获取队列信息
        
        Returns:
            队列状态信息
        """
        try:
            # 获取活动任务
            active_tasks = self.app.control.inspect().active()
            
            # 获取调度任务
            scheduled_tasks = self.app.control.inspect().scheduled()
            
            # 获取保留任务
            reserved_tasks = self.app.control.inspect().reserved()
            
            queue_info = {
                'timestamp': datetime.now().isoformat(),
                'active_tasks': active_tasks or {},
                'scheduled_tasks': scheduled_tasks or {},
                'reserved_tasks': reserved_tasks or {},
                'worker_stats': self._get_worker_stats()
            }
            
            return queue_info
            
        except Exception as e:
            self.logger.error(f"获取队列信息失败: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def _get_worker_stats(self) -> Dict:
        """获取Worker统计信息"""
        try:
            stats = self.app.control.inspect().stats()
            return stats or {}
        except:
            return {}
    
    def purge_queue(self, queue_name: str = None) -> Dict:
        """
        清空队列
        
        Args:
            queue_name: 队列名称，None表示清空所有队列
            
        Returns:
            清空结果
        """
        try:
            if queue_name:
                count = self.app.control.purge()
                message = f"队列 {queue_name} 已清空"
            else:
                count = self.app.control.purge()
                message = "所有队列已清空"
            
            return {
                'status': 'success',
                'purged_count': count,
                'message': message
            }
            
        except Exception as e:
            self.logger.error(f"清空队列失败: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }

def demo_basic_operations():
    """演示基础操作"""
    print("=" * 60)
    print("Celery消息队列基础操作演示")
    print("=" * 60)
    
    # 设置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 创建处理器
    handler = CeleryHandler()
    
    print("\n1. 提交简单任务")
    task_id1 = handler.submit_simple_task("Hello Celery!", delay=2)
    print(f"任务ID: {task_id1}")
    
    print("\n2. 获取任务状态")
    status = handler.get_task_status(task_id1)
    print(f"任务状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
    
    print("\n3. 等待任务完成")
    result = handler.wait_for_task(task_id1, timeout=10)
    print(f"任务结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    print("\n4. 提交批量任务")
    items = [f"项目_{i}" for i in range(1, 16)]
    task_id2 = handler.submit_batch_task(items, batch_size=5)
    print(f"批量任务ID: {task_id2}")
    
    print("\n5. 监控批量任务进度")
    start_time = time.time()
    while time.time() - start_time < 30:  # 最多等待30秒
        status = handler.get_task_status(task_id2)
        print(f"批量任务状态: {status.get('state', 'UNKNOWN')}")
        
        if status.get('state') == 'PROGRESS':
            progress = status.get('progress', {})
            print(f"  进度: {progress.get('message', '处理中...')}")
        elif status.get('ready'):
            print("批量任务完成!")
            break
        
        time.sleep(2)
    
    print("\n6. 提交长时间任务")
    task_id3 = handler.submit_long_task(duration=10, progress_updates=True)
    print(f"长时间任务ID: {task_id3}")
    
    print("\n7. 提交错误任务（演示重试）")
    task_id4 = handler.submit_error_task(should_fail=True, error_message="故意失败演示重试")
    print(f"错误任务ID: {task_id4}")
    
    print("\n8. 获取队列信息")
    queue_info = handler.get_queue_info()
    print(f"队列信息: {json.dumps(queue_info, indent=2, ensure_ascii=False, default=str)}")
    
    print("\n演示完成!")

if __name__ == "__main__":
    demo_basic_operations()
