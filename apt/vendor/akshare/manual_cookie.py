"""
手动设置东方财富网站Cookie
"""
import os
import sys
import time
from pathlib import Path

# 获取项目根目录
root_dir = Path(__file__).resolve().parent.parent.parent.parent

# 确保当前文件的父目录在sys.path中，这样可以导入同一目录下的模块
sys.path.append(str(Path(__file__).resolve().parent))

def write_cookie_to_file(cookie_str, file_path="eastmoney_cookie.txt"):
    """
    将Cookie写入文件
    """
    try:
        file_path = Path(file_path)
        if not file_path.is_absolute():
            file_path = root_dir / file_path
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cookie_str)
        print(f"Cookie已成功保存到: {file_path}")
        return True
    except Exception as e:
        print(f"保存Cookie到文件时出错: {e}")
        return False

def read_cookie_from_file(file_path="eastmoney_cookie.txt"):
    """
    从文件读取Cookie
    """
    try:
        file_path = Path(file_path)
        if not file_path.is_absolute():
            file_path = root_dir / file_path
            
        if not file_path.exists():
            print(f"Cookie文件不存在: {file_path}")
            return None
            
        with open(file_path, 'r', encoding='utf-8') as f:
            cookie_str = f.read().strip()
        
        if cookie_str:
            print(f"从文件成功读取Cookie: {file_path}")
            print(f"Cookie长度: {len(cookie_str)} 字符")
            return cookie_str
        else:
            print(f"Cookie文件为空: {file_path}")
            return None
    except Exception as e:
        print(f"读取Cookie文件时出错: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 如果提供了命令行参数，则将其作为Cookie
        cookie_str = sys.argv[1]
        write_cookie_to_file(cookie_str)
    else:
        # 没有参数时，提示用户输入
        print("请输入或粘贴从浏览器中复制的东方财富网站Cookie字符串:")
        cookie_str = input().strip()
        
        if cookie_str:
            write_cookie_to_file(cookie_str)
            print("\n保存成功！可以通过以下方式在代码中使用此Cookie:")
            print("-" * 60)
            print("from manual_cookie import read_cookie_from_file")
            print("cookie_str = read_cookie_from_file()")
            print("# 在请求中使用cookie_str")
            print("-" * 60)
        else:
            print("未输入Cookie，操作取消。")