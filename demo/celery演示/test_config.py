"""
配置测试脚本
用于验证 .env 文件配置是否正确
"""

import os
import sys
from dotenv import load_dotenv
from urllib.parse import urlparse
import mysql.connector
import redis

# 加载环境变量
load_dotenv()

def test_env_config():
    """测试环境变量配置"""
    print("=== 环境变量配置测试 ===")
    
    # 数据库相关
    db_name = os.getenv('DB_NAME', 'ubuntu186')
    print(f"DB_NAME: {db_name}")
    
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
    
    conn_env_key = connection_map.get(db_name.lower(), 'UBUNTU186_DB_CONN')
    db_conn_string = os.getenv(conn_env_key)
    
    print(f"使用连接字符串变量: {conn_env_key}")
    print(f"连接字符串: {db_conn_string}")
    
    # Redis 配置
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = os.getenv('REDIS_PORT', '6379')
    redis_password = os.getenv('REDIS_PASSWORD', '')
    
    print(f"Redis Host: {redis_host}")
    print(f"Redis Port: {redis_port}")
    print(f"Redis Password: {'***' if redis_password else '(empty)'}")
    
    return db_conn_string, redis_host, redis_port, redis_password

def parse_db_connection_string(db_conn_string):
    """解析数据库连接字符串"""
    if not db_conn_string:
        raise ValueError("数据库连接字符串为空")
    
    # 解析连接字符串 mysql+pymysql://user:password@host:port/database
    parsed = urlparse(db_conn_string)
    
    db_config = {
        'host': parsed.hostname,
        'port': parsed.port or 3306,
        'user': parsed.username,
        'password': parsed.password,
        'database': parsed.path.lstrip('/'),
        'charset': 'utf8mb4'
    }
    
    print("\n=== 解析后的数据库配置 ===")
    print(f"Host: {db_config['host']}")
    print(f"Port: {db_config['port']}")
    print(f"User: {db_config['user']}")
    print(f"Password: {'***' if db_config['password'] else '(empty)'}")
    print(f"Database: {db_config['database']}")
    print(f"Charset: {db_config['charset']}")
    
    return db_config

def test_mysql_connection(db_config):
    """测试 MySQL 连接"""
    print("\n=== MySQL 连接测试 ===")
    try:
        conn = mysql.connector.connect(**db_config)
        print("✓ MySQL 连接成功")
        
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"✓ MySQL 版本: {version[0]}")
        
        cursor.execute("SELECT DATABASE()")
        database = cursor.fetchone()
        print(f"✓ 当前数据库: {database[0]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except mysql.connector.Error as e:
        print(f"✗ MySQL 连接失败: {e}")
        return False

def test_redis_connection(redis_host, redis_port, redis_password):
    """测试 Redis 连接"""
    print("\n=== Redis 连接测试 ===")
    try:
        if redis_password:
            r = redis.Redis(host=redis_host, port=int(redis_port), password=redis_password, decode_responses=True)
        else:
            r = redis.Redis(host=redis_host, port=int(redis_port), decode_responses=True)
        
        # 测试连接
        r.ping()
        print("✓ Redis 连接成功")
        
        # 获取Redis信息
        info = r.info()
        print(f"✓ Redis 版本: {info['redis_version']}")
        print(f"✓ Redis 模式: {info['redis_mode']}")
        
        # 测试基本操作
        r.set('celery_test', 'test_value', ex=10)
        value = r.get('celery_test')
        print(f"✓ Redis 读写测试: {value}")
        
        return True
        
    except Exception as e:
        print(f"✗ Redis 连接失败: {e}")
        return False

def test_celery_config():
    """测试 Celery 配置"""
    print("\n=== Celery 配置测试 ===")
    
    try:
        # 导入 Celery 配置
        from celery_config import CELERY_CONFIG, DB_CONFIG, REDIS_URL
        
        print("✓ Celery 配置导入成功")
        print(f"✓ Broker URL: {REDIS_URL}")
        print(f"✓ Result Backend: {CELERY_CONFIG['result_backend']}")
        print(f"✓ 数据库配置: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Celery 配置测试失败: {e}")
        return False

def main():
    """主函数"""
    print("开始配置验证...")
    
    # 测试环境变量
    db_conn_string, redis_host, redis_port, redis_password = test_env_config()
    
    # 解析数据库配置
    try:
        db_config = parse_db_connection_string(db_conn_string)
    except Exception as e:
        print(f"数据库配置解析失败: {e}")
        return False
    
    # 测试数据库连接
    mysql_ok = test_mysql_connection(db_config)
    
    # 测试Redis连接
    redis_ok = test_redis_connection(redis_host, redis_port, redis_password)
    
    # 测试Celery配置
    celery_ok = test_celery_config()
    
    # 总结
    print("\n=== 配置验证总结 ===")
    print(f"MySQL 连接: {'✓' if mysql_ok else '✗'}")
    print(f"Redis 连接: {'✓' if redis_ok else '✗'}")
    print(f"Celery 配置: {'✓' if celery_ok else '✗'}")
    
    if mysql_ok and redis_ok and celery_ok:
        print("\n🎉 所有配置验证通过！可以启动 Celery 服务")
        return True
    else:
        print("\n❌ 部分配置验证失败，请检查相关配置")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
