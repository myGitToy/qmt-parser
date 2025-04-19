import os
import fitz  # PyMuPDF
import cv2
import numpy as np
import pytesseract
from PIL import Image
import io

def extract_image_from_pdf(pdf_path):
    """从PDF提取图片"""
    doc = fitz.open(pdf_path)
    images = []
    
    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        pix = page.get_pixmap()
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        images.append(np.array(img))
    
    doc.close()
    return images

def segment_large_image(image, max_height=4000):
    """将长图片分割成多个小图片"""
    height, width = image.shape[:2]
    
    # 如果图片高度小于阈值，直接返回
    if height <= max_height:
        return [image]
    
    # 计算需要分割的段数
    num_segments = (height + max_height - 1) // max_height
    segments = []
    
    for i in range(num_segments):
        start_y = i * max_height
        end_y = min(start_y + max_height, height)
        segment = image[start_y:end_y, :]
        segments.append(segment)
    
    return segments

def perform_ocr(image, lang='chi_sim+eng'):
    """对图片进行OCR识别"""
    # 转为PIL Image以便pytesseract处理
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)
    
    # 执行OCR
    text = pytesseract.image_to_string(image, lang=lang)
    return text

def process_pdf_ocr(pdf_path, lang='chi_sim+eng', max_height=4000):
    """处理PDF文件的完整OCR流程"""
    result_text = ""
    
    # 提取图片
    try:
        images = extract_image_from_pdf(pdf_path)
    except Exception as e:
        print(f"从PDF提取图片失败: {e}")
        return None
    
    # 处理每个图片
    for i, image in enumerate(images):
        print(f"处理第 {i+1} 页图片，尺寸: {image.shape}")
        
        # 分割图片
        segments = segment_large_image(image, max_height)
        print(f"图片分割为 {len(segments)} 个部分")
        
        # 对每个分段进行OCR
        for j, segment in enumerate(segments):
            print(f"  处理分段 {j+1}/{len(segments)}")
            text = perform_ocr(segment, lang)
            result_text += text + "\n\n"
            print(f"  分段 {j+1} OCR完成，识别了 {len(text)} 个字符")
    
    return result_text

def process_image_ocr(image_path, lang='chi_sim+eng', max_height=4000):
    """处理图片文件的OCR流程"""
    # 读取图像文件
    try:
        if isinstance(image_path, str):
            image = cv2.imread(image_path)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # OpenCV默认是BGR，转为RGB
        else:
            image = image_path  # 假设已经是numpy数组
    except Exception as e:
        print(f"读取图像失败: {e}")
        return None
    
    result_text = ""
    print(f"处理图像，尺寸: {image.shape}")
    
    # 分割图片
    segments = segment_large_image(image, max_height)
    print(f"图片分割为 {len(segments)} 个部分")
    
    # 对每个分段进行OCR
    for j, segment in enumerate(segments):
        print(f"  处理分段 {j+1}/{len(segments)}")
        text = perform_ocr(segment, lang)
        result_text += text + "\n\n"
        print(f"  分段 {j+1} OCR完成，识别了 {len(text)} 个字符")
    
    return result_text

# 使用示例
if __name__ == "__main__":
    # PDF路径
    pdf_file = "path/to/your/screenshot.pdf"
    
    # 如果是PDF文件
    if pdf_file.lower().endswith('.pdf'):
        text = process_pdf_ocr(pdf_file)
    # 如果是图片文件
    elif pdf_file.lower().endswith(('.png', '.jpg', '.jpeg')):
        text = process_image_ocr(pdf_file)
    else:
        print("不支持的文件格式")
        text = None
    
    # 保存结果
    if text:
        output_file = os.path.splitext(pdf_file)[0] + "_ocr.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"OCR结果已保存到: {output_file}")
