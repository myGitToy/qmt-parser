"""
目标：
1. 访问C:\CAAC下的所有pdf文件
2. 去除每一页页脚的水印： yinlei.org为航空和飞行模拟爱好者整理 ，本资料请不要用于实际飞行
"""

import os
import glob
import fitz  # PyMuPDF
import re
from pathlib import Path


def remove_watermark_from_pdf(input_path, output_path, watermark_text):
    """
    从PDF文件中去除指定的水印文本
    
    Args:
        input_path (str): 输入PDF文件路径
        output_path (str): 输出PDF文件路径
        watermark_text (str): 要去除的水印文本
    """
    try:
        # 打开PDF文档
        doc = fitz.open(input_path)
        
        # 遍历每一页
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # 获取页面上的所有文本块
            text_instances = page.search_for(watermark_text)
            
            # 如果找到水印文本，则删除它
            for inst in text_instances:
                # 创建一个白色矩形覆盖水印区域
                rect = fitz.Rect(inst)
                # 扩大矩形区域以确保完全覆盖
                rect.x0 -= 2
                rect.y0 -= 2
                rect.x1 += 2
                rect.y1 += 2
                
                # 用白色矩形覆盖水印
                page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
        
        # 保存修改后的PDF
        doc.save(output_path)
        doc.close()
        
        print(f"成功处理文件: {input_path}")
        return True
        
    except Exception as e:
        print(f"处理文件 {input_path} 时出错: {str(e)}")
        return False


def process_caac_pdfs():
    """
    处理C:\CAAC目录下的所有PDF文件
    """
    # 设置目录路径
    caac_dir = r"C:\CAAC"
    output_dir = r"C:\CAAC\processed"
    
    # 要去除的水印文本
    watermark_text = "yinlei.org为航空和飞行模拟爱好者整理 ，本资料请不要用于实际飞行"
    
    # 检查输入目录是否存在
    if not os.path.exists(caac_dir):
        print(f"错误: 目录 {caac_dir} 不存在")
        return
    
    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 查找所有PDF文件
    pdf_pattern = os.path.join(caac_dir, "*.pdf")
    pdf_files = glob.glob(pdf_pattern)
    
    if not pdf_files:
        print(f"在 {caac_dir} 目录下没有找到PDF文件")
        return
    
    print(f"找到 {len(pdf_files)} 个PDF文件")
    
    # 处理每个PDF文件
    success_count = 0
    for pdf_file in pdf_files:
        filename = os.path.basename(pdf_file)
        output_path = os.path.join(output_dir, f"cleaned_{filename}")
        
        print(f"正在处理: {filename}")
        
        if remove_watermark_from_pdf(pdf_file, output_path, watermark_text):
            success_count += 1
    
    print(f"\n处理完成! 成功处理 {success_count} 个文件，共 {len(pdf_files)} 个文件")
    print(f"处理后的文件保存在: {output_dir}")


def install_required_packages():
    """
    安装所需的Python包
    """
    import subprocess
    import sys
    
    required_packages = ['PyMuPDF']
    
    for package in required_packages:
        try:
            __import__(package.lower().replace('-', '_'))
            print(f"{package} 已安装")
        except ImportError:
            print(f"正在安装 {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])


if __name__ == "__main__":
    print("CAAC航图水印去除工具")
    print("=" * 40)
    
    # 首先检查并安装必要的包
    try:
        import fitz
        print("PyMuPDF 已安装")
    except ImportError:
        print("PyMuPDF 未安装，正在安装...")
        install_required_packages()
        import fitz
    
    # 开始处理PDF文件
    process_caac_pdfs()

