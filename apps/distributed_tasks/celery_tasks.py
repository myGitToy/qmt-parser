"""
Celery配置和任务定义
用于分布式处理股票数据更新任务
"""

from celery import Celery
import os
import sys
from datetime import datetime, timedelta
import pandas as pd
import akshare as ak
import time
import logging
from typing import Dict, Optional
import json

# 添加当前目录到Python路径，解决相对导入问题
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 添加父目录到Python路径
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Celery配置
class CeleryConfig:
    # Redis作为broker和backend
    broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
    
    # 任务路由
    task_routes = {
        'distributed_tasks.celery_tasks.process_stock_data': {'queue': 'stock_queue'},
        'distributed_tasks.celery_tasks.process_etf_data': {'queue': 'etf_queue'},
        'distributed_tasks.celery_tasks.store_data_to_mysql': {'queue': 'db_queue'},
    }
    
    # 任务序列化
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    
    # 时区设置
    timezone = 'Asia/Shanghai'
    enable_utc = True
    
    # 并发设置
    worker_concurrency = 4
    worker_prefetch_multiplier = 1
    
    # 任务超时设置
    task_soft_time_limit = 300  # 5分钟软超时
    task_time_limit = 600       # 10分钟硬超时
    
    # 结果过期时间
    result_expires = 3600       # 1小时
    
    # 任务重试设置
    task_acks_late = True
    worker_disable_rate_limits = False

# 创建Celery应用
app = Celery('stock_data_processor')
app.config_from_object(CeleryConfig)

# 数据类型映射（模仿akshare的dict结构）
KTYPE_MAPPING = {
    '1m': '1',
    '5m': '5',
    '15m': '15',
    '30m': '30',
    '60m': '60',
    '1d': 'daily'
}

@app.task(bind=True, name='distributed_tasks.celery_tasks.process_stock_data')
def process_stock_data(self, task_data: Dict) -> Dict:
    """
    处理股票数据任务（模仿akshare的update_sequence_launch逻辑）
    
    Args:
        task_data: 任务数据字典
        
    Returns:
        处理结果字典
    """
    task_id = task_data['task_id']
    code = task_data['code']
    start_date = task_data['start_date']
    end_date = task_data['end_date']
    ktype = task_data['type']
    myclass = task_data['class']
    
    try:
        logger.info(f"开始处理任务 {task_id}: {code} ({ktype})")
        
        # 获取akshare数据
        symbol = code[:6] if len(code) > 6 else code
        
        # 根据类别选择合适的akshare函数
        if myclass == 'stock':
            df_ak = ak.stock_zh_a_hist_min_em(
                symbol=symbol,
                start_date=f"{start_date} 00:00:00",
                end_date=f"{end_date} 23:59:59",
                period=KTYPE_MAPPING.get(ktype, '60'),
                adjust=''
            )
        elif myclass == 'etf':
            df_ak = ak.fund_etf_hist_min_em(
                symbol=symbol,
                start_date=f"{start_date} 00:00:00",
                end_date=f"{end_date} 23:59:59",
                period=KTYPE_MAPPING.get(ktype, '60'),
                adjust=''
            )
        else:
            raise ValueError(f"不支持的证券类别: {myclass}")
        
        # 数据预处理（模仿akshare的数据适配逻辑）
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
            
            # 成交量单位转换（手转换为股）
            if 'volume' in df_ak.columns:
                df_ak['volume'] = df_ak['volume'] * 100
                
            # 时间格式转换
            if 'date' in df_ak.columns:
                df_ak['date'] = pd.to_datetime(df_ak['date'])
        
        # 调用数据库存储任务
        if not df_ak.empty:
            store_task = store_data_to_mysql.delay({
                'task_id': task_id,
                'code': code,
                'ktype': ktype,
                'data': df_ak.to_json(orient='records', date_format='iso'),
                'start_date': start_date,
                'end_date': end_date
            })
            
            result = {
                'status': 'success',
                'task_id': task_id,
                'code': code,
                'rows_processed': len(df_ak),
                'db_task_id': store_task.id,
                'message': f"成功处理 {code} 数据，共 {len(df_ak)} 条记录"
            }
        else:
            result = {
                'status': 'success',
                'task_id': task_id,
                'code': code,
                'rows_processed': 0,
                'message': f"{code} 无新数据"
            }
        
        logger.info(f"任务 {task_id} 处理完成: {result['message']}")
        return result
        
    except Exception as e:
        error_msg = f"处理任务 {task_id} 失败: {str(e)}"
        logger.error(error_msg)
        
        # 重试逻辑
        if self.request.retries < 3:
            logger.info(f"任务 {task_id} 准备重试，第 {self.request.retries + 1} 次")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {
            'status': 'failed',
            'task_id': task_id,
            'code': code,
            'error': str(e),
            'message': error_msg
        }

@app.task(bind=True, name='distributed_tasks.celery_tasks.process_etf_data')
def process_etf_data(self, task_data: Dict) -> Dict:
    """
    处理ETF数据任务
    
    Args:
        task_data: 任务数据字典
        
    Returns:
        处理结果字典
    """
    # ETF数据处理逻辑与股票类似，但使用不同的akshare接口
    task_data['class'] = 'etf'  # 确保类别正确
    return process_stock_data.apply_async(args=[task_data]).get()

@app.task(bind=True, name='distributed_tasks.celery_tasks.store_data_to_mysql')
def store_data_to_mysql(self, data_package: Dict) -> Dict:
    """
    将数据存储到MySQL数据库
    
    Args:
        data_package: 数据包字典
        
    Returns:
        存储结果字典
    """
    task_id = data_package['task_id']
    code = data_package['code']
    ktype = data_package['ktype']
    
    try:
        # 从数据库连接模块导入（兼容导入方式）
        try:
            from .mysql_connector import MySQLConnector
        except ImportError:
            try:
                from mysql_connector import MySQLConnector
            except ImportError:
                from distributed_tasks.mysql_connector import MySQLConnector
        
        # 解析数据
        df_new = pd.read_json(data_package['data'], orient='records')
        df_new['date'] = pd.to_datetime(df_new['date'])
        
        # 创建数据库连接
        db_connector = MySQLConnector()
        
        # 获取现有数据进行差值比较
        start_date = data_package['start_date']
        end_date = data_package['end_date']
        
        df_existing = db_connector.get_existing_data(
            code=code,
            ktype=ktype,
            start_date=start_date,
            end_date=end_date
        )
        
        # 计算差值（新数据 - 现有数据）
        if not df_existing.empty:
            # 合并并去除重复，保留新数据
            df_combined = pd.concat([df_new, df_existing, df_existing])
            df_diff = df_combined.drop_duplicates(subset=['date'], keep=False)
        else:
            df_diff = df_new.copy()
        
        # 存储差值数据
        if not df_diff.empty:
            rows_inserted = db_connector.insert_data(
                data=df_diff,
                table_name=f'akshare_{ktype}',
                if_exists='append'
            )
            
            result = {
                'status': 'success',
                'task_id': task_id,
                'code': code,
                'ktype': ktype,
                'rows_inserted': rows_inserted,
                'message': f"成功存储 {code} 数据到数据库，新增 {rows_inserted} 条记录"
            }
        else:
            result = {
                'status': 'success',
                'task_id': task_id,
                'code': code,
                'ktype': ktype,
                'rows_inserted': 0,
                'message': f"{code} 无新数据需要存储"
            }
        
        logger.info(f"数据库任务 {task_id} 完成: {result['message']}")
        return result
        
    except Exception as e:
        error_msg = f"存储任务 {task_id} 失败: {str(e)}"
        logger.error(error_msg)
        
        # 重试逻辑
        if self.request.retries < 2:
            logger.info(f"存储任务 {task_id} 准备重试，第 {self.request.retries + 1} 次")
            raise self.retry(countdown=30 * (self.request.retries + 1))
        
        return {
            'status': 'failed',
            'task_id': task_id,
            'code': code,
            'error': str(e),
            'message': error_msg
        }

@app.task(name='distributed_tasks.celery_tasks.batch_process_codes')
def batch_process_codes(codes: list, 
                       start_date: str, 
                       end_date: str,
                       myclass: str = 'stock',
                       ktype: str = '60m',
                       priority: int = 0) -> Dict:
    """
    批量处理证券代码（模仿akshare的批量更新逻辑）
    
    Args:
        codes: 证券代码列表
        start_date: 开始日期
        end_date: 结束日期
        myclass: 证券类别
        ktype: K线类型
        priority: 优先级
        
    Returns:
        批量处理结果
    """
    try:
        from .redis_manager import RedisTaskManager
    except ImportError:
        try:
            from redis_manager import RedisTaskManager
        except ImportError:
            from distributed_tasks.redis_manager import RedisTaskManager
    
    # 创建Redis任务管理器
    redis_manager = RedisTaskManager()
    
    # 添加任务到队列
    task_count = redis_manager.add_task_sequence(
        code_list=codes,
        start_date=datetime.strptime(start_date, '%Y-%m-%d'),
        end_date=datetime.strptime(end_date, '%Y-%m-%d'),
        myclass=myclass,
        ktype=ktype,
        priority=priority
    )
    
    return {
        'status': 'success',
        'tasks_added': task_count,
        'codes_count': len(codes),
        'message': f"成功添加 {task_count} 个任务到队列"
    }

@app.task(name='distributed_tasks.celery_tasks.monitor_tasks')
def monitor_tasks() -> Dict:
    """
    监控任务执行状态
    
    Returns:
        监控结果字典
    """
    try:
        from .redis_manager import RedisTaskManager
    except ImportError:
        try:
            from redis_manager import RedisTaskManager
        except ImportError:
            from distributed_tasks.redis_manager import RedisTaskManager
    
    redis_manager = RedisTaskManager()
    stats = redis_manager.get_task_statistics()
    
    return {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'statistics': stats,
        'status': 'healthy' if stats['total_tasks'] >= 0 else 'unknown'
    }

# 定期任务配置
from celery.schedules import crontab

app.conf.beat_schedule = {
    # 每小时清理一次已完成的任务
    'cleanup-completed-tasks': {
        'task': 'distributed_tasks.celery_tasks.cleanup_tasks',
        'schedule': crontab(minute=0),  # 每小时执行
    },
    # 每5分钟监控一次任务状态
    'monitor-task-status': {
        'task': 'distributed_tasks.celery_tasks.monitor_tasks',
        'schedule': crontab(minute='*/5'),  # 每5分钟执行
    },
}

@app.task(name='distributed_tasks.celery_tasks.cleanup_tasks')
def cleanup_tasks() -> Dict:
    """
    清理已完成的任务
    
    Returns:
        清理结果
    """
    try:
        from .redis_manager import RedisTaskManager
    except ImportError:
        try:
            from redis_manager import RedisTaskManager
        except ImportError:
            from distributed_tasks.redis_manager import RedisTaskManager
    
    redis_manager = RedisTaskManager()
    deleted_count = redis_manager.clear_completed_tasks(older_than_hours=24)
    
    return {
        'status': 'success',
        'deleted_tasks': deleted_count,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

if __name__ == '__main__':
    # 启动worker的命令示例
    print("启动Celery Worker命令:")
    print("celery -A distributed_tasks.celery_tasks worker --loglevel=info --concurrency=4")
    print("\n启动Celery Beat调度器命令:")
    print("celery -A distributed_tasks.celery_tasks beat --loglevel=info")
    print("\n启动Celery监控命令:")
    print("celery -A distributed_tasks.celery_tasks flower")
