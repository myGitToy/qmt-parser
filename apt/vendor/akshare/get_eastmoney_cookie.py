"""
获取东方财富网站的Cookie并保存到.env文件中
"""
import os
from em_cookie_local import get_eastmoney_cookie
from pathlib import Path
from datetime import datetime

def update_env_file(cookie_str):
    """更新.env文件中的EASTMONEY_COOKIES"""
    root_path = Path(__file__).resolve().parent.parent.parent.parent
    env_path = root_path / '.env'
    
    # 读取现有内容
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    else:
        lines = []
    
    # 检查是否存在EASTMONEY_COOKIES
    cookie_line_index = None
    for i, line in enumerate(lines):
        if line.startswith('EASTMONEY_COOKIES='):
            cookie_line_index = i
            break
    
    # 更新或添加EASTMONEY_COOKIES
    if cookie_line_index is not None:
        lines[cookie_line_index] = f'EASTMONEY_COOKIES="{cookie_str}"\n'
    else:
        lines.append(f'EASTMONEY_COOKIES="{cookie_str}"\n')
    
    # 添加更新时间注释
    time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for i, line in enumerate(lines):
        if line.startswith('# EASTMONEY_COOKIES更新时间:'):
            lines[i] = f'# EASTMONEY_COOKIES更新时间: {time_str}\n'
            break
    else:
        lines.append(f'# EASTMONEY_COOKIES更新时间: {time_str}\n')
    
    # 写回文件
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"Cookie已成功更新到 {env_path}")
    print(f"更新时间: {time_str}")
    return True

if __name__ == "__main__":
    print("正在获取东方财富网站Cookie...")
    cookie_str = get_eastmoney_cookie()
    
    if cookie_str:
        print("\n获取成功！Cookie长度:", len(cookie_str))
        print("Cookie前100字符:", cookie_str[:100] + "..." if len(cookie_str) > 100 else cookie_str)
        
        # 更新.env文件
        update_env_file(cookie_str)
    else:
        print("获取Cookie失败。请确保：")
        print("1. 已在Chrome中登录东方财富网站")
        print("2. 如果Chrome正在运行，请尝试先关闭Chrome")
        print("3. 如果问题持续，请手动从浏览器复制Cookie并更新.env文件")