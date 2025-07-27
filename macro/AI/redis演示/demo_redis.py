import redis
import json
import time
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

"""
本模块 演示如何使用 Redis 进行数据存储和任务管理
使用 Redis 作为消息队列和数据存储的示例
redis基础信息从工作区根文件夹 .env 文件中读取
"""


class RedisDemo:
    def __init__(self):
        """初始化Redis连接"""
        # 加载环境变量
        load_dotenv()
        
        # 从.env文件读取Redis配置
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', 6379))
        self.redis_password = os.getenv('REDIS_PASSWORD', None)
        self.redis_db = int(os.getenv('REDIS_DB', 0))
        
        # 创建Redis连接
        self.redis_client = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            password=self.redis_password,
            db=self.redis_db,
            decode_responses=True
        )
        
        # 测试连接
        try:
            self.redis_client.ping()
            print("Redis连接成功")
        except redis.ConnectionError:
            print("Redis连接失败")
            raise

    def data_storage_demo(self):
        """演示Redis数据存储功能"""
        print("\n=== Redis 数据存储演示 ===")
        
        # 1. 字符串存储
        self.redis_client.set("user:1:name", "张三")
        self.redis_client.set("user:1:age", 25)
        print(f"用户姓名: {self.redis_client.get('user:1:name')}")
        print(f"用户年龄: {self.redis_client.get('user:1:age')}")
        
        # 2. 哈希存储
        user_data = {
            "name": "李四",
            "age": "30",
            "email": "lisi@example.com",
            "city": "北京"
        }
        self.redis_client.hset("user:2", mapping=user_data)
        stored_user = self.redis_client.hgetall("user:2")
        print(f"用户信息: {stored_user}")
        
        # 3. 列表存储
        tasks = ["任务1", "任务2", "任务3"]
        for task in tasks:
            self.redis_client.lpush("task_queue", task)
        
        queue_length = self.redis_client.llen("task_queue")
        print(f"任务队列长度: {queue_length}")
        
        # 4. 集合存储
        tags = ["python", "redis", "数据库", "缓存"]
        for tag in tags:
            self.redis_client.sadd("article:tags", tag)
        
        all_tags = self.redis_client.smembers("article:tags")
        print(f"文章标签: {all_tags}")

    def message_queue_demo(self):
        """演示Redis消息队列功能"""
        print("\n=== Redis 消息队列演示 ===")
        
        # 生产者：发送消息
        messages = [
            {"id": 1, "type": "email", "content": "发送邮件给用户"},
            {"id": 2, "type": "sms", "content": "发送短信验证码"},
            {"id": 3, "type": "push", "content": "推送通知消息"}
        ]
        
        for msg in messages:
            self.redis_client.lpush("message_queue", json.dumps(msg, ensure_ascii=False))
        
        print(f"已发送 {len(messages)} 条消息到队列")
        
        # 消费者：处理消息
        processed_count = 0
        while True:
            # 阻塞式获取消息，超时时间5秒
            result = self.redis_client.brpop("message_queue", timeout=5)
            if result is None:
                break
                
            queue_name, message_data = result
            message = json.loads(message_data)
            print(f"处理消息: {message}")
            processed_count += 1
            
            # 模拟处理时间
            time.sleep(0.5)
        
        print(f"共处理了 {processed_count} 条消息")

    def task_management_demo(self):
        """演示Redis任务管理功能"""
        print("\n=== Redis 任务管理演示 ===")
        
        # 创建任务
        tasks = [
            {"id": "task_001", "name": "数据备份", "status": "pending", "priority": 1},
            {"id": "task_002", "name": "报表生成", "status": "pending", "priority": 2},
            {"id": "task_003", "name": "清理日志", "status": "pending", "priority": 3}
        ]
        
        # 存储任务信息
        for task in tasks:
            task_key = f"task:{task['id']}"
            self.redis_client.hset(task_key, mapping=task)
            
            # 根据优先级加入有序集合
            self.redis_client.zadd("task_priority_queue", {task['id']: task['priority']})
        
        print("任务已创建并加入优先级队列")
        
        # 按优先级处理任务
        while True:
            # 获取最高优先级的任务
            task_ids = self.redis_client.zrange("task_priority_queue", 0, 0)
            if not task_ids:
                break
                
            task_id = task_ids[0]
            task_key = f"task:{task_id}"
            
            # 获取任务详情
            task_info = self.redis_client.hgetall(task_key)
            print(f"正在处理任务: {task_info}")
            
            # 更新任务状态
            self.redis_client.hset(task_key, "status", "completed")
            
            # 从队列中移除
            self.redis_client.zrem("task_priority_queue", task_id)
            
            # 模拟处理时间
            time.sleep(1)
        
        print("所有任务处理完成")

    def cache_demo(self):
        """演示Redis缓存功能"""
        print("\n=== Redis 缓存演示 ===")
        
        # 模拟数据库查询结果
        def expensive_query(user_id: int) -> Dict[str, Any]:
            """模拟耗时的数据库查询"""
            print(f"执行数据库查询，用户ID: {user_id}")
            time.sleep(2)  # 模拟查询耗时
            return {
                "user_id": user_id,
                "name": f"用户{user_id}",
                "profile": f"用户{user_id}的详细信息"
            }
        
        def get_user_with_cache(user_id: int) -> Dict[str, Any]:
            """带缓存的用户信息查询"""
            cache_key = f"user_cache:{user_id}"
            
            # 尝试从缓存获取
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                print(f"从缓存获取用户{user_id}信息")
                return json.loads(cached_data)
            
            # 缓存未命中，查询数据库
            print(f"缓存未命中，查询数据库")
            user_data = expensive_query(user_id)
            
            # 存储到缓存，设置过期时间300秒
            self.redis_client.setex(
                cache_key, 
                300, 
                json.dumps(user_data, ensure_ascii=False)
            )
            
            return user_data
        
        # 第一次查询（缓存未命中）
        start_time = time.time()
        user_data = get_user_with_cache(123)
        first_query_time = time.time() - start_time
        print(f"第一次查询耗时: {first_query_time:.2f}秒")
        
        # 第二次查询（缓存命中）
        start_time = time.time()
        user_data = get_user_with_cache(123)
        second_query_time = time.time() - start_time
        print(f"第二次查询耗时: {second_query_time:.2f}秒")
        
        print(f"缓存命中节省时间: {first_query_time - second_query_time:.2f}秒")

    def cleanup(self):
        """清理演示数据"""
        print("\n=== 清理演示数据 ===")
        
        keys_to_delete = [
            "user:1:name", "user:1:age", "user:2",
            "task_queue", "article:tags", "message_queue",
            "task_priority_queue", "user_cache:123"
        ]
        
        # 删除任务相关的键
        task_keys = self.redis_client.keys("task:*")
        keys_to_delete.extend(task_keys)
        
        if keys_to_delete:
            deleted_count = self.redis_client.delete(*keys_to_delete)
            print(f"已删除 {deleted_count} 个键")
        else:
            print("没有需要删除的键")

def main():
    """主函数"""
    try:
        demo = RedisDemo()
        
        # 运行各种演示
        demo.data_storage_demo()
        demo.message_queue_demo()
        demo.task_management_demo()
        demo.cache_demo()
        
        # 清理数据
        demo.cleanup()
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")

if __name__ == "__main__":
    main()