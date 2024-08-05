from pdf2image import convert_from_path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os

def pdf_to_non_searchable(input_pdf_path, output_pdf_path):
    # 将PDF转换为图像列表
    images = convert_from_path(input_pdf_path)
    
    # 创建一个新的PDF文件
    c = canvas.Canvas(output_pdf_path, pagesize=letter)
    
    for image in images:
        # 获取图像尺寸
        width, height = image.size
        
        # 确保输出PDF的页面大小与图像匹配
        c.setPageSize((width, height))
        
        # 将图像保存为临时文件
        image_path = 'temp.jpg'
        image.save(image_path)
        
        # 将图像绘制到PDF页面
        c.drawImage(image_path, 0, 0, width=width, height=height)
        
        # 结束当前页面
        c.showPage()
        
        # 删除临时图像文件
        os.remove(image_path)
    
    # 保存PDF文件
    c.save()

# 使用示例
input_pdf_path = 'c:\\demo_economy.pdf'
output_pdf_path = 'c:\\demo_economy2.pdf'
pdf_to_non_searchable(input_pdf_path, output_pdf_path)