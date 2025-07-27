"""
任务队列消费者
用于处理股票数据更新任务
模仿akshare的update_sequence_launch功能
"""

import sys
import os
import time
import signal
from datetime import datetime
from typing import Dict, Any, Optional
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
    from .celery_tasks import process_stock_data, process_etf_data
    from .mysql_connector import MySQLConnector
except ImportError:
    # 如果相对导入失败，使用绝对导入
    try:
        from redis_manager import RedisTaskManager
        from celery_tasks import process_stock_data, process_etf_data
        from mysql_connector import MySQLConnector
    except ImportError:
        # 最后尝试完整路径导入
        from distributed_tasks.redis_manager import RedisTaskManager
        from distributed_tasks.celery_tasks import process_stock_data, process_etf_data
        from distributed_tasks.mysql_connector import MySQLConnector

class TaskConsumer:
    """任务消费者类"""
    
    def __init__(self, 
                 redis_config: Optional[Dict] = None,
                 mysql_config: Optional[Dict] = None,
                 sleep_interval: float = 0.05):
        """
        初始化任务消费者
        
        Args:
            redis_config: Redis配置字典
            mysql_config: MySQL配置字典  
            sleep_interval: 任务处理间隔时间（秒）
        """
        self.logger = logging.getLogger(__name__)
        
        # 初始化Redis管理器
        if redis_config:
            self.redis_manager = RedisTaskManager(**redis_config)
        else:
            self.redis_manager = RedisTaskManager()
        
        # 初始化MySQL连接器
        self.mysql_config = mysql_config
        
        # 运行控制
        self.running = False
        self.sleep_interval = sleep_interval
        
        # 统计信息
        self.stats = {
            'tasks_processed': 0,
            'tasks_succeeded': 0,
            'tasks_failed': 0,
            'start_time': None,
            'last_task_time': None
        }
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器，用于优雅关闭"""
        self.logger.info(f"收到信号 {signum}，准备关闭消费者...")
        self.stop()
    
    def start_consumer(self, 
                      priority: int = 0, 
                      max_tasks: Optional[int] = None,
                      use_celery: bool = True) -> Dict[str, Any]:
        """
        启动任务消费者（模仿akshare的update_sequence_launch）
        
        Args:
            priority: 处理的任务优先级 (0=普通, 1=高优先级)
            max_tasks: 最大处理任务数，None表示无限制
            use_celery: 是否使用Celery分布式处理
            
        Returns:
            消费者运行结果
        """
        try:
            self.running = True
            self.stats['start_time'] = datetime.now()
            
            self.logger.info(f"启动任务消费者，优先级: {priority}, 使用Celery: {use_celery}")
            
            # 处理任务循环
            while self.running:
                # 获取待处理任务
                task_data = self.redis_manager.get_pending_task(
                    priority=priority, 
                    timeout=5
                )
                
                if task_data is None:
                    # 没有任务，短暂休眠
                    time.sleep(1)
                    continue
                
                # 处理任务
                if use_celery:
                    result = self._process_task_with_celery(task_data)
                else:
                    result = self._process_task_direct(task_data)
                
                # 更新统计信息
                self._update_stats(result)
                
                # 检查最大任务数限制
                if max_tasks and self.stats['tasks_processed'] >= max_tasks:
                    self.logger.info(f"达到最大任务数限制 {max_tasks}，停止消费者")
                    break
                
                # 任务间隔
                if self.sleep_interval > 0:
                    time.sleep(self.sleep_interval)
            
            # 生成最终报告
            end_time = datetime.now()
            duration = (end_time - self.stats['start_time']).total_seconds()
            
            final_report = {
                'status': 'completed',
                'priority': priority,
                'use_celery': use_celery,
                'start_time': self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'duration_seconds': duration,
                'tasks_processed': self.stats['tasks_processed'],
                'tasks_succeeded': self.stats['tasks_succeeded'],
                'tasks_failed': self.stats['tasks_failed'],
                'success_rate': (self.stats['tasks_succeeded'] / max(1, self.stats['tasks_processed'])) * 100,
                'avg_tasks_per_second': self.stats['tasks_processed'] / max(1, duration)
            }
            
            self.logger.info(f"消费者执行完成: {final_report}")
            return final_report
            
        except Exception as e:
            error_msg = f"消费者执行失败: {str(e)}"
            self.logger.error(error_msg)
            return {
                'status': 'failed',
                'error': error_msg,
                'stats': self.stats
            }
    
    def _process_task_with_celery(self, task_data: Dict) -> Dict[str, Any]:
        """
        使用Celery处理任务
        
        Args:
            task_data: 任务数据
            
        Returns:
            处理结果
        """
        try:
            task_id = task_data['task_id']
            myclass = task_data['class']
            
            self.logger.info(f"使用Celery处理任务 {task_id}")
            
            # 根据证券类别选择合适的Celery任务
            if myclass == 'stock':
                celery_task = process_stock_data.delay(task_data)
            elif myclass == 'etf':
                celery_task = process_etf_data.delay(task_data)
            else:
                raise ValueError(f"不支持的证券类别: {myclass}")
            
            # 更新任务状态
            self.redis_manager.update_task_status(
                task_id, 
                'submitted_to_celery',
                {'celery_task_id': celery_task.id}
            )
            
            return {
                'status': 'submitted',
                'task_id': task_id,
                'celery_task_id': celery_task.id,
                'message': f"任务 {task_id} 已提交到Celery队列"
            }
            
        except Exception as e:
            error_msg = f"Celery任务提交失败: {str(e)}"
            self.logger.error(error_msg)
            
            # 更新失败状态
            self.redis_manager.update_task_status(
                task_data['task_id'],
                'failed',
                {'error': str(e)}
            )
            
            return {
                'status': 'failed',
                'task_id': task_data['task_id'],
                'error': str(e)
            }
    
    def _process_task_direct(self, task_data: Dict) -> Dict[str, Any]:
        """
        直接处理任务（不使用Celery）
        
        Args:
            task_data: 任务数据
            
        Returns:
            处理结果
        """
        try:
            task_id = task_data['task_id']
            code = task_data['code']
            myclass = task_data['class']
            ktype = task_data['type']
            
            self.logger.info(f"直接处理任务 {task_id}: {code} ({ktype})")
            
            # 调用处理函数（需要模拟Celery任务的逻辑）
            if myclass == 'stock':
                result = self._process_stock_data_sync(task_data)
            elif myclass == 'etf':
                result = self._process_etf_data_sync(task_data)
            else:
                raise ValueError(f"不支持的证券类别: {myclass}")
            
            # 更新任务状态
            if result['status'] == 'success':
                self.redis_manager.update_task_status(
                    task_id,
                    'completed',
                    {
                        'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'rows_processed': result.get('rows_processed', 0)
                    }
                )
            else:
                self.redis_manager.update_task_status(
                    task_id,
                    'failed',
                    {'error': result.get('error', 'Unknown error')}
                )
            
            return result
            
        except Exception as e:
            error_msg = f"直接处理任务失败: {str(e)}"
            self.logger.error(error_msg)
            
            # 更新失败状态
            self.redis_manager.update_task_status(
                task_data['task_id'],
                'failed',
                {'error': str(e)}
            )
            
            return {
                'status': 'failed',
                'task_id': task_data['task_id'],
                'error': str(e)
            }
    
    def _process_stock_data_sync(self, task_data: Dict) -> Dict[str, Any]:
        """
        同步处理股票数据（简化版的Celery任务逻辑）
        
        Args:
            task_data: 任务数据
            
        Returns:
            处理结果
        """
        import akshare as ak
        import pandas as pd
        
        try:
            task_id = task_data['task_id']
            code = task_data['code']
            start_date = task_data['start_date']
            end_date = task_data['end_date']
            ktype = task_data['type']
            myclass = task_data['class']
            
            # 获取akshare数据
            symbol = code[:6] if len(code) > 6 else code
            
            # K线类型映射
            ktype_mapping = {
                '1m': '1',
                '5m': '5', 
                '15m': '15',
                '30m': '30',
                '60m': '60',
                '1d': 'daily'
            }
            
            if myclass == 'stock':
                df_ak = ak.stock_zh_a_hist_min_em(
                    symbol=symbol,
                    start_date=f"{start_date} 00:00:00",
                    end_date=f"{end_date} 23:59:59",
                    period=ktype_mapping.get(ktype, '60'),
                    adjust=''
                )
            elif myclass == 'etf':
                df_ak = ak.fund_etf_hist_min_em(
                    symbol=symbol,
                    start_date=f"{start_date} 00:00:00",
                    end_date=f"{end_date} 23:59:59",
                    period=ktype_mapping.get(ktype, '60'),
                    adjust=''
                )
            else:
                raise ValueError(f"不支持的证券类别: {myclass}")
            
            # 数据预处理
            if not df_ak.empty:
                # 删除不需要的列
                if ktype == '1m':
                    if '均价' in df_ak.columns:
                        df_ak.drop(columns=['均价'], inplace=True)
                elif ktype in ['60m', '30m', '5m']:
                    drop_cols = ['涨跌幅', '涨跌额', '振幅', '换手率']
                    existing_cols = [col for col in drop_cols if col in df_ak.columns]
                    if existing_cols:
                        df_ak.drop(columns=existing_cols, inplace=True)
                
                # 添加代码列
                df_ak['code'] = code
                
                # 重命名列
                column_mapping = {
                    "时间": "date",
                    "开盘": "open",
                    "收盘": "close",
                    "最高": "high", 
                    "最低": "low",
                    "成交量": "volume",
                    "成交额": "money"
                }
                df_ak.rename(columns=column_mapping, errors='ignore', inplace=True)
                
                # 成交量单位转换
                if 'volume' in df_ak.columns:
                    df_ak['volume'] = df_ak['volume'] * 100
                    
                # 时间格式转换
                if 'date' in df_ak.columns:
                    df_ak['date'] = pd.to_datetime(df_ak['date'])
                
                # 存储到数据库
                with MySQLConnector(self.mysql_config) as db:
                    # 确保表存在
                    db.create_table_if_not_exists(ktype)
                    
                    # 获取现有数据进行差值比较
                    df_existing = db.get_existing_data(
                        code=code,
                        ktype=ktype,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    # 计算差值
                    if not df_existing.empty:
                        df_combined = pd.concat([df_ak, df_existing, df_existing])
                        df_diff = df_combined.drop_duplicates(subset=['date'], keep=False)
                    else:
                        df_diff = df_ak.copy()
                    
                    # 存储差值数据
                    if not df_diff.empty:
                        rows_inserted = db.insert_data(
                            data=df_diff,
                            table_name=f'akshare_{ktype}',
                            if_exists='append'
                        )
                        
                        return {
                            'status': 'success',
                            'task_id': task_id,
                            'code': code,
                            'rows_processed': len(df_ak),
                            'rows_inserted': rows_inserted,
                            'message': f"成功处理 {code} 数据，新增 {rows_inserted} 条记录"
                        }
                    else:
                        return {
                            'status': 'success',
                            'task_id': task_id,
                            'code': code,
                            'rows_processed': len(df_ak),
                            'rows_inserted': 0,
                            'message': f"{code} 无新数据需要存储"
                        }
            else:
                return {
                    'status': 'success',
                    'task_id': task_id,
                    'code': code,
                    'rows_processed': 0,
                    'rows_inserted': 0,
                    'message': f"{code} 无数据返回"
                }
                
        except Exception as e:
            return {
                'status': 'failed',
                'task_id': task_data['task_id'],
                'code': task_data['code'],
                'error': str(e)
            }
    
    def _process_etf_data_sync(self, task_data: Dict) -> Dict[str, Any]:
        """
        同步处理ETF数据
        
        Args:
            task_data: 任务数据
            
        Returns:
            处理结果
        """
        # ETF数据处理逻辑与股票相同
        task_data['class'] = 'etf'
        return self._process_stock_data_sync(task_data)
    
    def _update_stats(self, result: Dict[str, Any]):
        """
        更新统计信息
        
        Args:
            result: 任务处理结果
        """
        self.stats['tasks_processed'] += 1
        self.stats['last_task_time'] = datetime.now()
        
        if result['status'] in ['success', 'submitted']:
            self.stats['tasks_succeeded'] += 1
        else:
            self.stats['tasks_failed'] += 1
    
    def stop(self):
        """停止消费者"""
        self.running = False
        self.logger.info("任务消费者停止运行")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取消费者统计信息
        
        Returns:
            统计信息字典
        """
        current_time = datetime.now()
        
        stats_copy = self.stats.copy()
        
        if stats_copy['start_time']:
            stats_copy['running_duration'] = (current_time - stats_copy['start_time']).total_seconds()
            stats_copy['start_time'] = stats_copy['start_time'].strftime('%Y-%m-%d %H:%M:%S')
        
        if stats_copy['last_task_time']:
            stats_copy['last_task_time'] = stats_copy['last_task_time'].strftime('%Y-%m-%d %H:%M:%S')
        
        stats_copy['is_running'] = self.running
        stats_copy['current_time'] = current_time.strftime('%Y-%m-%d %H:%M:%S')
        
        return stats_copy

if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    # 创建任务消费者
    consumer = TaskConsumer(sleep_interval=0.1)
    
    # 获取初始统计信息
    initial_stats = consumer.get_stats()
    print(f"初始统计信息: {initial_stats}")
    
    # 启动消费者（处理少量任务用于测试）
    print("启动任务消费者...")
    try:
        result = consumer.start_consumer(
            priority=1,  # 处理高优先级任务
            max_tasks=5,  # 最多处理5个任务
            use_celery=False  # 使用直接处理模式
        )
        print(f"消费者执行结果: {result}")
    except KeyboardInterrupt:
        print("用户中断消费者执行")
    
    # 获取最终统计信息
    final_stats = consumer.get_stats()
    print(f"最终统计信息: {final_stats}")
