#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 MinioHandler 配置是否正确
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apt.os.minio.MinioHandler import MinioClientWrapper
from dotenv import load_dotenv

def test_minio_config():
    """测试 Minio 配置"""
    print("正在测试 Minio 配置...")
    
    # 加载环境变量
    load_dotenv()
    
    # 打印环境变量
    print(f"minio_ENDPOINT: {os.getenv('minio_ENDPOINT')}")
    print(f"minio_ACCESS_KEY: {os.getenv('minio_ACCESS_KEY')}")
    print(f"minio_SECRET_KEY: {os.getenv('minio_SECRET_KEY')}")
    print(f"minio_CACHE_PATH: {os.getenv('minio_CACHE_PATH')}")
    
    try:
        # 创建 MinioClientWrapper 实例
        minio_client = MinioClientWrapper()
        print("✓ MinioClientWrapper 初始化成功")
        print(f"✓ 缓存路径: {minio_client.MINIO_CACHE_PATH}")
        
        # 测试连接
        buckets = minio_client.list_buckets()
        print("✓ 成功连接到 Minio 服务器")
        print(f"✓ 发现 {len(buckets)} 个存储桶")
        print(buckets)
        
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_minio_config()
    if success:
        print("\n🎉 Minio 配置测试通过！")
    else:
        print("\n❌ Minio 配置测试失败！")
