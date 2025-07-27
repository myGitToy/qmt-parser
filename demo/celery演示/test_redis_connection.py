"""
Redis 连接测试脚本
用于测试 Redis 连接是否正常工作
"""

import os
import sys
import redis
from dotenv import load_dotenv

def test_redis_connection():
    """测试Redis连接"""
    try:
        # 加载环境变量
        load_dotenv()
        
        # 获取Redis配置
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        redis_password = os.getenv('REDIS_PASSWORD', '')
        
        print(f"连接到 Redis: {redis_host}:{redis_port}")
        
        # 创建Redis连接
        if redis_password:
            r = redis.Redis(host=redis_host, port=redis_port, password=redis_password, db=0)
        else:
            r = redis.Redis(host=redis_host, port=redis_port, db=0)
        
        # 测试连接
        r.ping()
        print("✓ Redis 连接成功！")
        
        # 测试基本操作
        print("\n测试基本操作...")
        
        # 设置值
        r.set('test_key', 'test_value')
        print("✓ 设置键值对成功")
        
        # 获取值
        value = r.get('test_key')
        print(f"✓ 获取值成功: {value.decode('utf-8')}")
        
        # 删除测试键
        r.delete('test_key')
        print("✓ 删除测试键成功")
        
        # 获取Redis信息
        info = r.info()
        print(f"\nRedis 服务器信息:")
        print(f"- 版本: {info['redis_version']}")
        print(f"- 内存使用: {info['used_memory_human']}")
        print(f"- 连接数: {info['connected_clients']}")
        print(f"- 运行天数: {info['uptime_in_days']}")
        
        return True
        
    except redis.ConnectionError as e:
        print(f"❌ Redis 连接失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_celery_redis_config():
    """测试Celery Redis配置"""
    try:
        # 加载环境变量
        load_dotenv()
        
        # 获取Redis配置
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = os.getenv('REDIS_PORT', '6379')
        redis_password = os.getenv('REDIS_PASSWORD', '')
        
        # 构建Redis连接URL
        if redis_password:
            redis_url = f'redis://:{redis_password}@{redis_host}:{redis_port}/0'
        else:
            redis_url = f'redis://{redis_host}:{redis_port}/0'
        
        print(f"Celery Redis URL: {redis_url}")
        
        # 测试连接
        r = redis.from_url(redis_url)
        r.ping()
        print("✓ Celery Redis 配置有效！")
        
        return True
        
    except Exception as e:
        print(f"❌ Celery Redis 配置测试失败: {e}")
        return False

if __name__ == '__main__':
    print("=== Redis 连接测试 ===")
    
    # 测试基本连接
    if test_redis_connection():
        print("\n=== Celery Redis 配置测试 ===")
        test_celery_redis_config()
    else:
        print("\n请检查Redis服务是否正在运行，或者检查配置信息是否正确。")
        sys.exit(1)
    
    print("\n✓ 所有测试完成！")
