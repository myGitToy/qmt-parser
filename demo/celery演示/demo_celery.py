"""
Celery 证券数据更新任务模板
用于批量执行MySQL中待更新表的证券数据更新任务
"""

from celery import Celery
from celery.result import AsyncResult
import mysql.connector
from typing import List, Dict, Any
import logging
from datetime import datetime
import time
import os
from dotenv import load_dotenv
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 解析数据库连接字符串
def parse_db_connection_string():
    """解析数据库连接字符串"""
    db_name = os.getenv('DB_NAME', 'ubuntu186').lower()
    
    # 根据DB_NAME选择对应的连接字符串
    connection_map = {
        'aliyun': 'ALIYUN_DB_CONN',
        'aws': 'AWS_DB_CONN',
        'localhost': 'LOCAL_DB_CONN',
        'centos9': 'CENTOS9_DB_CONN',
        'ubuntu186': 'UBUNTU186_DB_CONN',
        'ubuntu191': 'UBUNTU191_DB_CONN',
        'docker_201': 'docker_201_DB_CONN'
    }
    
    conn_env_key = connection_map.get(db_name, 'UBUNTU186_DB_CONN')
    db_conn_string = os.getenv(conn_env_key)
    
    if not db_conn_string:
        raise ValueError(f"未找到数据库连接字符串: {conn_env_key}")
    
    # 解析连接字符串 mysql+pymysql://user:password@host:port/database
    parsed = urlparse(db_conn_string)
    
    return {
        'host': parsed.hostname,
        'port': parsed.port or 3306,
        'user': parsed.username,
        'password': parsed.password,
        'database': parsed.path.lstrip('/'),
        'charset': 'utf8mb4'
    }

# 获取数据库配置
DB_CONFIG = parse_db_connection_string()

# 创建Celery应用
app = Celery('securities_data_updater')

# Redis配置
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')

# 构建Redis连接URL
if REDIS_PASSWORD:
    REDIS_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0'
else:
    REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'

# Celery配置
app.conf.update(
    broker_url=REDIS_URL,  # Redis作为消息代理
    result_backend=REDIS_URL,  # Redis作为结果存储
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_routes={
        'securities_data_updater.update_single_security': {'queue': 'securities_update'},
        'securities_data_updater.batch_update_securities': {'queue': 'batch_update'},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
)

# 打印配置信息
logger.info(f"数据库配置: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
logger.info(f"Redis配置: {REDIS_HOST}:{REDIS_PORT}")

class SecurityDataUpdater:
    """证券数据更新器"""
    
    def __init__(self):
        self.db_config = DB_CONFIG
        
    def get_db_connection(self):
        """获取数据库连接"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            return conn
        except mysql.connector.Error as e:
            logger.error(f"数据库连接错误: {e}")
            raise
    
    def get_pending_updates(self, table_name: str = 'securities_update_queue') -> List[Dict]:
        """获取待更新的证券列表"""
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            query = f"""
            SELECT id, security_code, security_name, update_type, priority, created_at
            FROM {table_name} 
            WHERE status = 'pending'
            ORDER BY priority DESC, created_at ASC
            """
            cursor.execute(query)
            results = cursor.fetchall()
            return results
        except mysql.connector.Error as e:
            logger.error(f"获取待更新任务失败: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def update_task_status(self, task_id: int, status: str, error_msg: str = None):
        """更新任务状态"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            query = """
            UPDATE securities_update_queue 
            SET status = %s, updated_at = %s, error_message = %s
            WHERE id = %s
            """
            cursor.execute(query, (status, datetime.now(), error_msg, task_id))
            conn.commit()
        except mysql.connector.Error as e:
            logger.error(f"更新任务状态失败: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

# 创建数据更新器实例
updater = SecurityDataUpdater()

@app.task(bind=True, max_retries=3, default_retry_delay=60)
def update_single_security(self, security_info: Dict[str, Any]):
    """
    更新单个证券数据的任务
    
    Args:
        security_info: 包含证券信息的字典
            - id: 任务ID
            - security_code: 证券代码
            - security_name: 证券名称
            - update_type: 更新类型 (price, volume, technical, all)
    """
    task_id = security_info['id']
    security_code = security_info['security_code']
    security_name = security_info['security_name']
    update_type = security_info['update_type']
    
    try:
        logger.info(f"开始更新证券 {security_code} ({security_name}) - 类型: {update_type}")
        
        # 更新任务状态为进行中
        updater.update_task_status(task_id, 'processing')
        
        # 这里添加具体的证券数据更新逻辑
        # 例如：调用tushare、akshare或其他数据接口
        success = update_security_data(security_code, update_type)
        
        if success:
            updater.update_task_status(task_id, 'completed')
            logger.info(f"证券 {security_code} 更新完成")
            return {
                'status': 'success',
                'security_code': security_code,
                'message': f'证券 {security_code} 更新成功'
            }
        else:
            updater.update_task_status(task_id, 'failed', '数据更新失败')
            raise Exception(f"证券 {security_code} 数据更新失败")
            
    except Exception as e:
        logger.error(f"更新证券 {security_code} 失败: {str(e)}")
        updater.update_task_status(task_id, 'failed', str(e))
        
        # 如果还有重试次数，则重试
        if self.request.retries < self.max_retries:
            logger.info(f"任务重试 ({self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)
        
        return {
            'status': 'failed',
            'security_code': security_code,
            'error': str(e)
        }

@app.task(bind=True)
def batch_update_securities(self, batch_size: int = 10):
    """
    批量更新证券数据任务
    
    Args:
        batch_size: 批次大小，默认10
    """
    try:
        # 获取待更新的任务列表
        pending_tasks = updater.get_pending_updates()
        
        if not pending_tasks:
            logger.info("没有待更新的任务")
            return {'status': 'success', 'message': '没有待更新的任务'}
        
        logger.info(f"找到 {len(pending_tasks)} 个待更新任务")
        
        # 分批处理任务
        results = []
        for i in range(0, len(pending_tasks), batch_size):
            batch = pending_tasks[i:i + batch_size]
            batch_results = []
            
            # 并行提交批次内的任务
            for task in batch:
                result = update_single_security.delay(task)
                batch_results.append({
                    'task_id': task['id'],
                    'security_code': task['security_code'],
                    'celery_task_id': result.id
                })
            
            results.extend(batch_results)
            
            # 批次间稍作延迟，避免过载
            if i + batch_size < len(pending_tasks):
                time.sleep(1)
        
        return {
            'status': 'success',
            'total_tasks': len(pending_tasks),
            'batch_size': batch_size,
            'submitted_tasks': results
        }
        
    except Exception as e:
        logger.error(f"批量更新任务失败: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e)
        }

@app.task
def get_task_status(celery_task_id: str):
    """获取任务状态"""
    result = AsyncResult(celery_task_id, app=app)
    return {
        'task_id': celery_task_id,
        'status': result.status,
        'result': result.result,
        'traceback': result.traceback
    }

def update_security_data(security_code: str, update_type: str) -> bool:
    """
    具体的证券数据更新逻辑
    这里需要根据实际需求实现具体的数据获取和更新逻辑
    
    Args:
        security_code: 证券代码
        update_type: 更新类型
        
    Returns:
        bool: 更新是否成功
    """
    try:
        # 模拟数据更新过程
        logger.info(f"正在更新 {security_code} 的 {update_type} 数据")
        
        # 这里添加具体的数据更新逻辑
        # 例如：
        # if update_type == 'price':
        #     update_price_data(security_code)
        # elif update_type == 'volume':
        #     update_volume_data(security_code)
        # elif update_type == 'technical':
        #     update_technical_data(security_code)
        # elif update_type == 'all':
        #     update_all_data(security_code)
        
        # 模拟处理时间
        time.sleep(2)
        
        return True
        
    except Exception as e:
        logger.error(f"更新证券 {security_code} 数据失败: {e}")
        return False

# 辅助函数
def submit_batch_update(batch_size: int = 10):
    """提交批量更新任务"""
    result = batch_update_securities.delay(batch_size)
    return result.id

def check_task_result(task_id: str):
    """检查任务结果"""
    result = AsyncResult(task_id, app=app)
    return {
        'task_id': task_id,
        'status': result.status,
        'result': result.result,
        'ready': result.ready(),
        'successful': result.successful() if result.ready() else None
    }

if __name__ == '__main__':
    # 启动Celery worker
    # 命令: celery -A demo_celery worker --loglevel=info --queues=securities_update,batch_update
    app.start()