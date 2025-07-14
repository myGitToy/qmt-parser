"""
将证券数据写入Redis的脚本
"""

import redis
import json
from datetime import datetime
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# Redis配置
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')

# 创建Redis连接
def get_redis_connection():
    """获取Redis连接"""
    if REDIS_PASSWORD:
        return redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            decode_responses=True
        )
    else:
        return redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )

# 数据
securities_data = [
    {
        "id": 7035772,
        "code": "300677.SZ",
        "start_date": "2025-07-10 08:00:00",
        "end_date": "2025-07-14 18:55:26",
        "class": "stock",
        "type": "1m",
        "priority": 1
    },
    {
        "id": 7035773,
        "code": "300678.SZ",
        "start_date": "2025-07-10 08:00:00",
        "end_date": "2025-07-14 18:55:26",
        "class": "stock",
        "type": "1m",
        "priority": 1
    },
    {
        "id": 7035774,
        "code": "300679.SZ",
        "start_date": "2025-07-10 08:00:00",
        "end_date": "2025-07-14 18:55:26",
        "class": "stock",
        "type": "1m",
        "priority": 1
    },
    {
        "id": 7035775,
        "code": "300680.SZ",
        "start_date": "2025-07-10 08:00:00",
        "end_date": "2025-07-14 18:55:26",
        "class": "stock",
        "type": "1m",
        "priority": 1
    },
    {
        "id": 7035776,
        "code": "300681.SZ",
        "start_date": "2025-07-10 08:00:00",
        "end_date": "2025-07-14 18:55:26",
        "class": "stock",
        "type": "1m",
        "priority": 1
    }
]

def write_data_to_redis():
    """将数据写入Redis"""
    try:
        # 连接Redis
        r = get_redis_connection()
        
        # 测试连接
        r.ping()
        print(f"成功连接到Redis: {REDIS_HOST}:{REDIS_PORT}")
        
        # 方法1: 使用Hash存储每个证券的详细信息
        print("\n=== 方法1: 使用Hash存储 ===")
        for data in securities_data:
            key = f"security:{data['code']}"
            r.hset(key, mapping=data)
            print(f"已存储: {key}")
        
        # 方法2: 使用List存储待处理任务队列
        print("\n=== 方法2: 使用List存储任务队列 ===")
        queue_key = "securities_update_queue"
        r.delete(queue_key)  # 清空现有队列
        
        for data in securities_data:
            r.lpush(queue_key, json.dumps(data))
            print(f"已添加到队列: {data['code']}")
        
        queue_length = r.llen(queue_key)
        print(f"队列长度: {queue_length}")
        
        # 方法3: 使用Sorted Set按优先级存储
        print("\n=== 方法3: 使用Sorted Set按优先级存储 ===")
        priority_key = "securities_priority_queue"
        r.delete(priority_key)  # 清空现有队列
        
        for data in securities_data:
            # 使用priority作为score，id作为member
            r.zadd(priority_key, {json.dumps(data): data['priority']})
            print(f"已添加到优先级队列: {data['code']} (优先级: {data['priority']})")
        
        priority_queue_length = r.zcard(priority_key)
        print(f"优先级队列长度: {priority_queue_length}")
        
        # 方法4: 使用Set存储证券代码集合
        print("\n=== 方法4: 使用Set存储证券代码集合 ===")
        codes_key = "securities_codes"
        r.delete(codes_key)  # 清空现有集合
        
        for data in securities_data:
            r.sadd(codes_key, data['code'])
            print(f"已添加到代码集合: {data['code']}")
        
        codes_count = r.scard(codes_key)
        print(f"代码集合大小: {codes_count}")
        
        print("\n=== 数据写入完成 ===")
        return True
        
    except redis.ConnectionError as e:
        print(f"Redis连接错误: {e}")
        return False
    except Exception as e:
        print(f"写入数据时发生错误: {e}")
        return False

def read_data_from_redis():
    """从Redis读取数据验证"""
    try:
        r = get_redis_connection()
        
        print("\n=== 验证Redis中的数据 ===")
        
        # 读取Hash数据
        print("\n1. Hash数据:")
        for data in securities_data:
            key = f"security:{data['code']}"
            hash_data = r.hgetall(key)
            if hash_data:
                print(f"  {key}: {hash_data}")
        
        # 读取List数据
        print("\n2. List队列数据:")
        queue_key = "securities_update_queue"
        queue_data = r.lrange(queue_key, 0, -1)
        for i, item in enumerate(queue_data):
            data = json.loads(item)
            print(f"  位置{i}: {data['code']} (ID: {data['id']})")
        
        # 读取Sorted Set数据
        print("\n3. Sorted Set优先级队列数据:")
        priority_key = "securities_priority_queue"
        priority_data = r.zrange(priority_key, 0, -1, withscores=True)
        for item, score in priority_data:
            data = json.loads(item)
            print(f"  {data['code']} (优先级: {score})")
        
        # 读取Set数据
        print("\n4. Set代码集合数据:")
        codes_key = "securities_codes"
        codes_data = r.smembers(codes_key)
        print(f"  代码集合: {sorted(codes_data)}")
        
        return True
        
    except Exception as e:
        print(f"读取数据时发生错误: {e}")
        return False

def clear_redis_data():
    """清空Redis中的测试数据"""
    try:
        r = get_redis_connection()
        
        # 要清空的keys
        keys_to_clear = [
            "securities_update_queue",
            "securities_priority_queue",
            "securities_codes"
        ]
        
        # 清空Hash数据
        for data in securities_data:
            keys_to_clear.append(f"security:{data['code']}")
        
        # 删除所有keys
        deleted_count = 0
        for key in keys_to_clear:
            if r.exists(key):
                r.delete(key)
                deleted_count += 1
                print(f"已删除: {key}")
        
        print(f"\n总共删除了 {deleted_count} 个key")
        return True
        
    except Exception as e:
        print(f"清空数据时发生错误: {e}")
        return False

if __name__ == "__main__":
    print("=== Redis数据写入脚本 ===")
    print(f"Redis配置: {REDIS_HOST}:{REDIS_PORT}")
    
    # 写入数据
    if write_data_to_redis():
        print("\n✅ 数据写入成功")
        
        # 验证数据
        if read_data_from_redis():
            print("\n✅ 数据验证成功")
        
        # 询问是否清空数据
        choice = input("\n是否清空测试数据？(y/n): ").lower()
        if choice == 'y':
            clear_redis_data()
            print("✅ 数据清空完成")
    else:
        print("\n❌ 数据写入失败")