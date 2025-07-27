"""
Celery 配置文件
"""

import os
from dotenv import load_dotenv
from urllib.parse import urlparse

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
        'charset': 'utf8mb4',
        'autocommit': True
    }

# Redis 配置
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = 0
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')

# 构建Redis连接URL
if REDIS_PASSWORD:
    REDIS_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
else:
    REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

# MySQL 数据库配置
DB_CONFIG = parse_db_connection_string()

# Celery 配置
CELERY_CONFIG = {
    'broker_url': REDIS_URL,
    'result_backend': REDIS_URL,
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'Asia/Shanghai',
    'enable_utc': True,
    'task_routes': {
        'demo_celery.update_single_security': {'queue': 'securities_update'},
        'demo_celery.batch_update_securities': {'queue': 'batch_update'},
    },
    'worker_prefetch_multiplier': 1,
    'task_acks_late': True,
    'worker_max_tasks_per_child': 1000,
    'task_time_limit': 300,  # 5分钟超时
    'task_soft_time_limit': 240,  # 4分钟软超时
}

# 日志配置
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'celery_securities.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'celery': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'securities_data_updater': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
