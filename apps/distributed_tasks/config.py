"""
配置文件
分布式任务系统的配置管理
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """配置类"""
    
    # Redis配置
    REDIS_CONFIG = {
        'host': os.getenv('REDIS_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_PORT', 6379)),
        'db': int(os.getenv('REDIS_DB', 0)),
        'password': os.getenv('REDIS_PASSWORD'),
        'decode_responses': True
    }
    
    # MySQL配置
    MYSQL_CONFIG = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'myfunds'),
        'charset': os.getenv('MYSQL_CHARSET', 'utf8mb4')
    }
    
    # Celery配置
    CELERY_CONFIG = {
        'broker_url': os.getenv('CELERY_BROKER_URL', f"redis://{REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}/1"),
        'result_backend': os.getenv('CELERY_RESULT_BACKEND', f"redis://{REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}/2"),
        'task_serializer': 'json',
        'result_serializer': 'json',
        'accept_content': ['json'],
        'timezone': 'Asia/Shanghai',
        'enable_utc': True,
        'worker_concurrency': int(os.getenv('CELERY_WORKER_CONCURRENCY', 4)),
        'task_soft_time_limit': int(os.getenv('CELERY_TASK_SOFT_TIME_LIMIT', 300)),
        'task_time_limit': int(os.getenv('CELERY_TASK_TIME_LIMIT', 600)),
        'result_expires': int(os.getenv('CELERY_RESULT_EXPIRES', 3600)),
    }
    
    # 任务处理配置
    TASK_CONFIG = {
        'default_sleep_interval': float(os.getenv('TASK_SLEEP_INTERVAL', 0.05)),
        'max_retry_attempts': int(os.getenv('TASK_MAX_RETRIES', 3)),
        'batch_size': int(os.getenv('TASK_BATCH_SIZE', 1000)),
        'data_retention_hours': int(os.getenv('DATA_RETENTION_HOURS', 24)),
    }
    
    # akshare数据配置
    AKSHARE_CONFIG = {
        'ktype_mapping': {
            '1m': '1',
            '5m': '5',
            '15m': '15', 
            '30m': '30',
            '60m': '60',
            '1d': 'daily'
        },
        'supported_classes': ['stock', 'etf'],
        'supported_ktypes': ['1m', '5m', '15m', '30m', '60m', '1d'],
        'max_rows_per_request': int(os.getenv('AKSHARE_MAX_ROWS', 8000)),
    }
    
    # 日志配置
    LOGGING_CONFIG = {
        'level': os.getenv('LOG_LEVEL', 'INFO'),
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file_path': os.getenv('LOG_FILE_PATH', 'logs/distributed_tasks.log'),
        'max_file_size': int(os.getenv('LOG_MAX_FILE_SIZE', 10485760)),  # 10MB
        'backup_count': int(os.getenv('LOG_BACKUP_COUNT', 5)),
    }
    
    @classmethod
    def get_redis_config(cls) -> Dict[str, Any]:
        """获取Redis配置"""
        return cls.REDIS_CONFIG.copy()
    
    @classmethod
    def get_mysql_config(cls) -> Dict[str, Any]:
        """获取MySQL配置"""
        return cls.MYSQL_CONFIG.copy()
    
    @classmethod
    def get_celery_config(cls) -> Dict[str, Any]:
        """获取Celery配置"""
        return cls.CELERY_CONFIG.copy()
    
    @classmethod
    def get_all_config(cls) -> Dict[str, Any]:
        """获取所有配置"""
        return {
            'redis': cls.get_redis_config(),
            'mysql': cls.get_mysql_config(),
            'celery': cls.get_celery_config(),
            'task': cls.TASK_CONFIG.copy(),
            'akshare': cls.AKSHARE_CONFIG.copy(),
            'logging': cls.LOGGING_CONFIG.copy(),
        }
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """验证配置"""
        issues = []
        
        # 检查必需的环境变量
        required_vars = [
            ('MYSQL_PASSWORD', 'MySQL密码'),
            ('REDIS_HOST', 'Redis主机'),
            ('MYSQL_HOST', 'MySQL主机'),
        ]
        
        for var_name, description in required_vars:
            if not os.getenv(var_name):
                issues.append(f"缺少环境变量 {var_name} ({description})")
        
        # 检查数值配置的合理性
        if cls.TASK_CONFIG['default_sleep_interval'] < 0:
            issues.append("任务间隔时间不能为负数")
        
        if cls.AKSHARE_CONFIG['max_rows_per_request'] <= 0:
            issues.append("最大请求行数必须大于0")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }

# 开发环境配置
class DevelopmentConfig(Config):
    """开发环境配置"""
    
    REDIS_CONFIG = Config.REDIS_CONFIG.copy()
    REDIS_CONFIG.update({
        'db': 1,  # 使用不同的数据库
    })
    
    MYSQL_CONFIG = Config.MYSQL_CONFIG.copy()
    MYSQL_CONFIG.update({
        'database': 'myfunds_dev',
    })
    
    TASK_CONFIG = Config.TASK_CONFIG.copy()
    TASK_CONFIG.update({
        'default_sleep_interval': 0.1,  # 开发环境更快的处理速度
        'data_retention_hours': 1,  # 更短的数据保留时间
    })

# 生产环境配置
class ProductionConfig(Config):
    """生产环境配置"""
    
    TASK_CONFIG = Config.TASK_CONFIG.copy()
    TASK_CONFIG.update({
        'default_sleep_interval': 0.05,  # 生产环境的实际速度
        'max_retry_attempts': 5,  # 更多的重试次数
        'data_retention_hours': 72,  # 更长的数据保留时间
    })
    
    LOGGING_CONFIG = Config.LOGGING_CONFIG.copy()
    LOGGING_CONFIG.update({
        'level': 'WARNING',  # 生产环境减少日志输出
    })

# 测试环境配置
class TestingConfig(Config):
    """测试环境配置"""
    
    REDIS_CONFIG = Config.REDIS_CONFIG.copy()
    REDIS_CONFIG.update({
        'db': 2,  # 使用独立的测试数据库
    })
    
    MYSQL_CONFIG = Config.MYSQL_CONFIG.copy()
    MYSQL_CONFIG.update({
        'database': 'myfunds_test',
    })
    
    TASK_CONFIG = Config.TASK_CONFIG.copy()
    TASK_CONFIG.update({
        'default_sleep_interval': 0.01,  # 测试环境最快速度
        'max_retry_attempts': 1,  # 测试环境不重试
        'data_retention_hours': 0.1,  # 测试数据快速清理
    })

# 配置工厂函数
def get_config(env: str = None) -> Config:
    """
    获取配置对象
    
    Args:
        env: 环境名称 ('development', 'production', 'testing')
        
    Returns:
        配置对象
    """
    if env is None:
        env = os.getenv('ENVIRONMENT', 'development')
    
    config_map = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig,
    }
    
    return config_map.get(env, DevelopmentConfig)

if __name__ == "__main__":
    # 测试配置
    print("=== 配置测试 ===")
    
    # 测试默认配置
    config = Config()
    print(f"默认配置验证: {config.validate_config()}")
    
    # 测试不同环境配置
    for env_name in ['development', 'production', 'testing']:
        env_config = get_config(env_name)
        print(f"\n{env_name} 环境配置:")
        print(f"Redis DB: {env_config.REDIS_CONFIG['db']}")
        print(f"MySQL DB: {env_config.MYSQL_CONFIG['database']}")
        print(f"睡眠间隔: {env_config.TASK_CONFIG['default_sleep_interval']}")
        print(f"数据保留: {env_config.TASK_CONFIG['data_retention_hours']} 小时")
    
    # 输出完整配置示例
    print(f"\n=== 完整配置示例 ===")
    all_config = Config.get_all_config()
    for section, settings in all_config.items():
        print(f"\n[{section.upper()}]")
        for key, value in settings.items():
            print(f"{key} = {value}")
