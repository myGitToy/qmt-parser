"""
Redis数据结构管理器
用于管理股票数据更新任务的Redis存储结构
"""

import redis
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

class RedisTaskManager:
    """Redis任务数据管理器"""
    
    def __init__(self, 
                 host='192.169.1.201', 
                 port=6379, 
                 db=0, 
                 password=None,
                 decode_responses=True):
        """
        初始化Redis连接
        
        Args:
            host: Redis服务器地址
            port: Redis端口
            db: 数据库编号
            password: 密码
            decode_responses: 是否解码响应
        """
        self.redis_client = redis.Redis(
            host=host, 
            port=port, 
            db=db, 
            password=password,
            decode_responses=decode_responses
        )
        
        # 键前缀
        self.TASK_QUEUE_PREFIX = "task_queue"
        self.TASK_STATUS_PREFIX = "task_status"
        self.TASK_RESULT_PREFIX = "task_result"
        self.SEQUENCE_SET_PREFIX = "sequence_set"
        self.CACHE_PREFIX = "data_cache"
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
    
    def add_task_sequence(self, 
                         code_list: List[str], 
                         start_date: datetime, 
                         end_date: datetime,
                         myclass: str = 'stock',
                         ktype: str = '60m',
                         priority: int = 0) -> int:
        """
        添加任务序列到Redis（模仿akshare的update_sequence_add）
        
        Args:
            code_list: 证券代码列表
            start_date: 开始日期
            end_date: 结束日期  
            myclass: 证券类别 ('stock', 'etf')
            ktype: K线类型 ('1m', '5m', '60m', '1d')
            priority: 优先级 (0=普通, 1=高优先级)
            
        Returns:
            添加的任务数量
        """
        task_count = 0
        
        for code in code_list:
            task_data = {
                'code': code,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'class': myclass,
                'type': ktype,
                'priority': priority,
                'status': 'pending',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'task_id': f"{code}_{myclass}_{ktype}_{int(datetime.now().timestamp())}"
            }
            
            # 根据优先级选择队列
            queue_name = f"{self.TASK_QUEUE_PREFIX}:priority_{priority}"
            
            # 将任务添加到Redis列表（队列）
            self.redis_client.lpush(queue_name, json.dumps(task_data))
            
            # 添加到序列集合（用于去重和查询）
            sequence_key = f"{self.SEQUENCE_SET_PREFIX}:{myclass}_{ktype}"
            self.redis_client.sadd(sequence_key, task_data['task_id'])
            
            # 设置任务状态
            status_key = f"{self.TASK_STATUS_PREFIX}:{task_data['task_id']}"
            self.redis_client.hset(status_key, mapping={
                'status': 'pending',
                'created_at': task_data['created_at'],
                'code': code,
                'class': myclass,
                'type': ktype
            })
            
            task_count += 1
            
        self.logger.info(f"添加了 {task_count} 个任务到队列 priority_{priority}")
        return task_count
    
    def get_pending_task(self, priority: int = 0, timeout: int = 5) -> Optional[Dict]:
        """
        获取待处理任务（模仿akshare的update_sequence_launch逻辑）
        
        Args:
            priority: 优先级
            timeout: 阻塞超时时间（秒）
            
        Returns:
            任务数据字典或None
        """
        queue_name = f"{self.TASK_QUEUE_PREFIX}:priority_{priority}"
        
        # 使用阻塞式右弹出（BRPOP）获取任务
        result = self.redis_client.brpop(queue_name, timeout=timeout)
        
        if result:
            queue, task_json = result
            task_data = json.loads(task_json)
            
            # 更新任务状态为处理中
            self.update_task_status(task_data['task_id'], 'processing', {
                'started_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            return task_data
        
        return None
    
    def update_task_status(self, task_id: str, status: str, extra_data: Dict = None):
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 状态 ('pending', 'processing', 'completed', 'failed')
            extra_data: 额外数据
        """
        status_key = f"{self.TASK_STATUS_PREFIX}:{task_id}"
        
        update_data = {
            'status': status,
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if extra_data:
            update_data.update(extra_data)
            
        self.redis_client.hset(status_key, mapping=update_data)
    
    def cache_stock_data(self, 
                        code: str, 
                        ktype: str, 
                        data: pd.DataFrame, 
                        expire_seconds: int = 3600):
        """
        缓存股票数据
        
        Args:
            code: 证券代码
            ktype: K线类型
            data: 数据DataFrame
            expire_seconds: 过期时间（秒）
        """
        cache_key = f"{self.CACHE_PREFIX}:{code}_{ktype}"
        
        # 将DataFrame转换为JSON存储
        cache_data = {
            'data': data.to_json(orient='records', date_format='iso'),
            'cached_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'rows': len(data)
        }
        
        self.redis_client.setex(
            cache_key, 
            expire_seconds, 
            json.dumps(cache_data)
        )
    
    def get_cached_data(self, code: str, ktype: str) -> Optional[pd.DataFrame]:
        """
        获取缓存的股票数据
        
        Args:
            code: 证券代码
            ktype: K线类型
            
        Returns:
            DataFrame或None
        """
        cache_key = f"{self.CACHE_PREFIX}:{code}_{ktype}"
        cached_json = self.redis_client.get(cache_key)
        
        if cached_json:
            cache_data = json.loads(cached_json)
            df = pd.read_json(cache_data['data'], orient='records')
            df['date'] = pd.to_datetime(df['date'])
            return df
        
        return None
    
    def get_queue_length(self, priority: int = 0) -> int:
        """
        获取队列长度
        
        Args:
            priority: 优先级
            
        Returns:
            队列中任务数量
        """
        queue_name = f"{self.TASK_QUEUE_PREFIX}:priority_{priority}"
        return self.redis_client.llen(queue_name)
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """
        获取任务统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            'queue_lengths': {},
            'task_counts_by_status': {},
            'total_tasks': 0
        }
        
        # 获取各优先级队列长度
        for priority in [0, 1]:
            queue_name = f"{self.TASK_QUEUE_PREFIX}:priority_{priority}"
            length = self.redis_client.llen(queue_name)
            stats['queue_lengths'][f'priority_{priority}'] = length
            stats['total_tasks'] += length
        
        # 获取任务状态统计
        status_pattern = f"{self.TASK_STATUS_PREFIX}:*"
        status_keys = self.redis_client.keys(status_pattern)
        
        status_counts = {'pending': 0, 'processing': 0, 'completed': 0, 'failed': 0}
        
        for key in status_keys:
            task_status = self.redis_client.hget(key, 'status')
            if task_status in status_counts:
                status_counts[task_status] += 1
        
        stats['task_counts_by_status'] = status_counts
        
        return stats
    
    def clear_completed_tasks(self, older_than_hours: int = 24):
        """
        清理已完成的任务记录
        
        Args:
            older_than_hours: 清理多少小时前的记录
        """
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        cutoff_str = cutoff_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # 查找已完成且超过时间的任务
        status_pattern = f"{self.TASK_STATUS_PREFIX}:*"
        status_keys = self.redis_client.keys(status_pattern)
        
        deleted_count = 0
        
        for key in status_keys:
            task_info = self.redis_client.hgetall(key)
            if (task_info.get('status') in ['completed', 'failed'] and 
                task_info.get('updated_at', '') < cutoff_str):
                
                # 删除状态记录
                self.redis_client.delete(key)
                
                # 删除结果缓存
                task_id = key.split(':')[-1]
                result_key = f"{self.TASK_RESULT_PREFIX}:{task_id}"
                self.redis_client.delete(result_key)
                
                deleted_count += 1
        
        self.logger.info(f"清理了 {deleted_count} 个过期任务记录")
        return deleted_count
    
    def health_check(self) -> Dict[str, Any]:
        """
        Redis健康检查
        
        Returns:
            健康状态信息
        """
        try:
            # 测试连接
            self.redis_client.ping()
            
            # 获取Redis信息
            info = self.redis_client.info()
            
            return {
                'status': 'healthy',
                'redis_version': info.get('redis_version'),
                'connected_clients': info.get('connected_clients'),
                'used_memory_human': info.get('used_memory_human'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace': info.get('keyspace', {})
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    # 创建Redis任务管理器
    redis_manager = RedisTaskManager()
    
    # 健康检查
    health = redis_manager.health_check()
    print(f"Redis健康状态: {health}")
    
    # 添加测试任务
    test_codes = ['000001', '000002', '000858']
    start_date = datetime(2024, 6, 20)
    end_date = datetime.now()
    
    task_count = redis_manager.add_task_sequence(
        code_list=test_codes,
        start_date=start_date,
        end_date=end_date,
        myclass='stock',
        ktype='1m',
        priority=1
    )
    
    print(f"添加了 {task_count} 个测试任务")
    
    # 获取统计信息
    stats = redis_manager.get_task_statistics()
    print(f"任务统计: {stats}")
