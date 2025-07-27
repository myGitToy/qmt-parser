#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 RustfsHandler 配置是否正确（使用大写环境变量）
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apt.os.rustfs.RustfsHandler import RustfsClientWrapper
from dotenv import load_dotenv

def test_rustfs_config():
    """测试 Rustfs 配置"""
    print("正在测试 Rustfs 配置...")
    
    # 加载环境变量
    load_dotenv()
    
    # 打印环境变量
    print(f"RUSTFS_ENDPOINT: {os.getenv('RUSTFS_ENDPOINT')}")
    print(f"RUSTFS_ACCESS_KEY: {os.getenv('RUSTFS_ACCESS_KEY')}")
    print(f"RUSTFS_SECRET_KEY: {os.getenv('RUSTFS_SECRET_KEY')}")
    print(f"RUSTFS_CACHE_PATH: {os.getenv('RUSTFS_CACHE_PATH')}")
    
    try:
        # 创建 RustfsClientWrapper 实例
        rustfs_client = RustfsClientWrapper()
        print("✓ RustfsClientWrapper 初始化成功")
        print(f"✓ 缓存路径: {rustfs_client.RUSTFS_CACHE_PATH}")
        
        # 测试连接
        buckets = rustfs_client.list_buckets()
        print("✓ 成功连接到 Rustfs 服务器")
        print(f"✓ 发现 {len(buckets)} 个存储桶")
        if len(buckets) > 0:
            print(buckets)
        
        # 测试文件存在性检查
        test_file = "test-file.txt"
        test_bucket = "test-bucket"
        exists = rustfs_client.file_exists(test_bucket, test_file)
        print(f"✓ 文件存在性检查功能正常: {exists}")
        
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_rustfs_config()
    if success:
        print("\n🎉 Rustfs 配置测试通过！")
    else:
        print("\n❌ Rustfs 配置测试失败！")
