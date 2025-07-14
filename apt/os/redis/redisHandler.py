"""
将证券数据写入Redis的脚本
"""

import redis
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import os


class RedisClientWrapper():
    """Redis客户端封装"""
    
    def __init__(self, host='localhost', port=6379, password=None):
        # 加载环境变量
        load_dotenv()
        # Redis配置
        self.HOST = os.getenv('REDIS_HOST', 'localhost')
        self.PORT = int(os.getenv('REDIS_PORT', '6379'))
        self.PASSWORD = os.getenv('REDIS_PASSWORD', '')
        self.client = self.__get_redis_connection()
        self.dataFrame = pd.DataFrame()

    def __get_redis_connection(self):
        """获取Redis连接"""
        if self.PASSWORD:
            return redis.Redis(
                host=self.HOST,
                port=self.PORT,
                password=self.PASSWORD,
                decode_responses=True
            )
        else:
            return redis.Redis(
                host=self.HOST,
                port=self.PORT,
                decode_responses=True
            )


    def add_task(self, task_dataframe, redis_key="task101", **kwargs):
        """
        通用任务添加系统，输入redis_key和task_dataframe
        兼容的任务清单有：
            task101: akshare 1m->5m重采样
            task102: akshare 1m->60m重采样
        """
        for _, row in task_dataframe.iterrows():
            task_data = {
                "code": row.get('code'),
                "start_date": row.get('start_date').strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(row.get('start_date')) else None,
                "end_date": row.get('end_date').strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(row.get('end_date')) else None
            }
            self.client.rpush(redis_key, json.dumps(task_data, ensure_ascii=False))

    def add_task101(self, task_dataframe,  **kwargs):
        """
        101号任务 akshare 1m->5m重采样
        key: task101
        存储方式：Redis List
        数据类型："code": "300681.SZ", "start_date": "2025-07-10 08:00:00", "end_date": "2025-07-14 18:55:26"
        
        Args:
            task_dataframe: 任务数据框
            redis_key: Redis键名，默认为"task101"
            **kwargs: 其他可选参数
        """
        redis_key = "task101"
        for _, row in task_dataframe.iterrows():
            task_data = {
                "code": row.get('code'),
                "start_date": row.get('start_date').strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(row.get('start_date')) else None,
                "end_date": row.get('end_date').strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(row.get('end_date')) else None
            }
            self.client.rpush(redis_key, json.dumps(task_data, ensure_ascii=False))

    def add_task102(self, task_dataframe,  **kwargs):
        """
        102号任务 akshare 1m->60m重采样
        key: task102
        存储方式：Redis List
        数据类型："code": "300681.SZ", "start_date": "2025-07-10 08:00:00", "end_date": "2025-07-14 18:55:26"
        
        Args:
            task_dataframe: 任务数据框
            redis_key: Redis键名，默认为"task102"
            **kwargs: 其他可选参数
        """
        redis_key = "task102"
        for _, row in task_dataframe.iterrows():
            task_data = {
                "code": row.get('code'),
                "start_date": row.get('start_date').strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(row.get('start_date')) else None,
                "end_date": row.get('end_date').strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(row.get('end_date')) else None
            }
            self.client.rpush(redis_key, json.dumps(task_data, ensure_ascii=False))