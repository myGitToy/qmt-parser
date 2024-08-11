import os
import zipfile

def compress_directory(directory_path, output_zip_path):
    # 确保输出目录存在
    output_dir = os.path.dirname(output_zip_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                zip_file.write(file_path, arcname=file_path.replace(directory_path, ''))

# 使用示例
start_dir = 'C:\\skii\\original' # 替换为您的起始目录路径
output_zip = 'C:\\skii\\zip' # 替换为您的输出压缩文件路径
compress_directory(start_dir, output_zip)
