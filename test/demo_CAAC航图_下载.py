"""
目标：
1. 访问view-source:https://yinlei.org/x-plane10/-aip-china.html网页
2. 根据网页源代码，查找/x-plane10/view.php?file=doc/ZSWX.pdf等类似的pdf页面，其中ZSWX为机场名，标准格式为ZXXX，XXX是英文字母
3. 上述页面对应的真实下载地址为：https://yinlei.org/x-plane10/doc/ZSWX.pdf
4. 下载该文件
5. 下载目录为c:\CAAC ，没有此目录则创建
"""

import os
import re
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time

def create_download_directory(download_dir):
    """创建下载目录，如果不存在则创建"""
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
        print(f"创建目录: {download_dir}")
    else:
        print(f"目录已存在: {download_dir}")

def get_webpage_content(url):
    """获取网页内容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        return response.text
    except requests.RequestException as e:
        print(f"请求网页失败: {e}")
        return None

def find_airport_pdf_links(html_content, base_url):
    """查找机场PDF文件的view.php链接并转换为直接下载链接"""
    pdf_links = []
    airport_codes = []
    
    # 查找类似 /x-plane10/view.php?file=doc/ZXXX.pdf 的链接
    # 其中 ZXXX 是机场代码格式 (Z + 3个字母)
    view_pattern = r'/x-plane10/view\.php\?file=doc/(Z[A-Z]{3})\.pdf'
    matches = re.findall(view_pattern, html_content, re.IGNORECASE)
    
    print(f"在源代码中找到 {len(matches)} 个机场代码:")
    
    for airport_code in matches:
        airport_code = airport_code.upper()  # 确保大写
        airport_codes.append(airport_code)
        
        # 构建直接下载链接
        direct_pdf_url = f"https://yinlei.org/x-plane10/doc/{airport_code}.pdf"
        pdf_links.append(direct_pdf_url)
        print(f"  - {airport_code}: {direct_pdf_url}")
    
    # 去重
    pdf_links = list(dict.fromkeys(pdf_links))
    
    # 也尝试查找其他可能的PDF链接格式
    try:
        # 查找直接的PDF链接
        direct_pdf_pattern = r'href=["\']([^"\']*\.pdf[^"\']*)["\']'
        direct_matches = re.findall(direct_pdf_pattern, html_content, re.IGNORECASE)
        
        for match in direct_matches:
            if 'doc/' in match and any(code in match.upper() for code in airport_codes):
                full_url = urljoin(base_url, match)
                if full_url not in pdf_links:
                    pdf_links.append(full_url)
    except Exception as e:
        print(f"查找直接PDF链接失败: {e}")
    
    return pdf_links, airport_codes

def check_pdf_availability(url):
    """检查PDF文件是否可访问"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.head(url, headers=headers, timeout=10)
        return response.status_code == 200
    except:
        return False

def download_file(url, download_dir, filename=None):
    """下载文件"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"开始下载: {url}")
        response = requests.get(url, headers=headers, stream=True, timeout=60)
        response.raise_for_status()
        
        # 确定文件名
        if not filename:
            # 从URL获取文件名
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            if not filename or not filename.endswith('.pdf'):
                filename = f"download_{int(time.time())}.pdf"
        
        # 确保文件名是有效的
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        filepath = os.path.join(download_dir, filename)
        
        # 下载文件
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f"下载完成: {filepath}")
        return filepath
        
    except requests.RequestException as e:
        print(f"下载失败 {url}: {e}")
        return None
    except Exception as e:
        print(f"保存文件失败: {e}")
        return None

def main():
    """主程序"""
    # 配置
    target_url = "https://yinlei.org/x-plane10/-aip-china.html"
    download_dir = r"c:\CAAC"
    
    print("CAAC航图下载器")
    print("=" * 50)
    
    # 创建下载目录
    create_download_directory(download_dir)
    
    # 获取网页内容
    print(f"正在访问: {target_url}")
    html_content = get_webpage_content(target_url)
    
    if not html_content:
        print("无法获取网页内容，程序退出")
        return
    
    # 查找机场PDF链接
    print("正在查找机场PDF文件链接...")
    pdf_links, airport_codes = find_airport_pdf_links(html_content, target_url)
    
    if not pdf_links:
        print("未找到机场PDF文件链接")
        print("检查网页源代码中是否包含类似 '/x-plane10/view.php?file=doc/ZXXX.pdf' 的链接")
        return
    
    print(f"\n找到 {len(pdf_links)} 个机场PDF文件:")
    for i, (link, code) in enumerate(zip(pdf_links, airport_codes), 1):
        print(f"{i}. {code}: {link}")
    
    # 检查文件可用性
    print("\n正在检查文件可用性...")
    available_links = []
    for i, (pdf_url, code) in enumerate(zip(pdf_links, airport_codes), 1):
        print(f"检查 {i}/{len(pdf_links)}: {code}")
        if check_pdf_availability(pdf_url):
            available_links.append((pdf_url, code))
            print(f"  ✓ 可用")
        else:
            print(f"  ✗ 不可用")
    
    if not available_links:
        print("没有可用的PDF文件")
        return
    
    print(f"\n有 {len(available_links)} 个文件可下载:")
    for pdf_url, code in available_links:
        print(f"  - {code}: {pdf_url}")
    
    # 下载所有可用的PDF文件
    print("\n开始下载PDF文件...")
    downloaded_files = []
    
    for i, (pdf_url, code) in enumerate(available_links, 1):
        print(f"\n下载进度: {i}/{len(available_links)} - {code}")
        filename = f"{code}.pdf"  # 使用机场代码作为文件名
        filepath = download_file(pdf_url, download_dir, filename)
        if filepath:
            downloaded_files.append((filepath, code))
        
        # 添加延迟避免请求过于频繁
        time.sleep(1)
    
    # 显示下载结果
    print("\n" + "=" * 50)
    print("下载完成!")
    print(f"成功下载 {len(downloaded_files)} 个文件:")
    for filepath, code in downloaded_files:
        print(f"  - {code}: {filepath}")
    
    if len(downloaded_files) < len(available_links):
        failed_count = len(available_links) - len(downloaded_files)
        print(f"有 {failed_count} 个文件下载失败")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"程序运行出错: {e}")
        import traceback
        traceback.print_exc()
