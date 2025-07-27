#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试从Redis task101队列中获取任务并进行5分钟重采样的功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apt.vendor.akshare.data import data
from apt.os.redis.redisHandler import RedisClientWrapper as redisClient

def test_task_process():
    """测试任务处理功能"""
    print("=== 测试Redis Task101任务处理 ===")
    
    # 创建数据实例
    akdata = data(myauth=True)
    
    # 检查Redis连接
    rds = redisClient()
    rds_conn = rds.client
    
    # 检查队列状态
    if rds_conn.exists('task101'):
        queue_length = rds_conn.llen('task101')
        print(f"Redis task101队列长度: {queue_length}")
        
        if queue_length > 0:
            # 执行任务处理
            akdata.task_process_task101()
        else:
            print("队列为空，无任务需要处理")
    else:
        print("task101队列不存在")

def test_resample_accuracy():
    """测试重采样准确性"""
    print("\n=== 测试5分钟重采样准确性 ===")
    
    # 创建数据实例
    akdata = data(myauth=True)
    
    # 执行测试
    result = akdata.test_resample_5m_accuracy()
    
    if result:
        print("✅ 测试通过")
    else:
        print("❌ 测试失败")

if __name__ == "__main__":
    # 测试任务处理
    test_task_process()
    
    # 测试重采样准确性
    test_resample_accuracy()
