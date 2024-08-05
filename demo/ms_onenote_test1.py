"""
pyOneNote is a lightweight python library to read OneNote files. The main goal of this parser is to allow cybersecurity analyst to extract useful information from OneNote files.
pyOneNote是一个轻量级的Python库，用于读取OneNote文件。该解析器的主要目标是允许网络安全分析师从OneNote文件中提取有用的信息。
参考资料：https://github.com/DissectMalware/pyOneNote/blob/main/README.md

使用方法：进入myfund根目录，运行以下命令
pyonenote -f "C:\\Users\\george\\AppData\\Local\\Microsoft\\OneNote\\16.0\\备份\\财新网（存档）\\2022达沃斯论坛.one (于 2024-4-5).one" -o "C:\\onenote_testfile" -e "txt"
"""
import os
import sys
import argparse
from pyOneNote.Header import *
from pyOneNote.FileNode import *
from pyOneNote.OneDocument import *
from pyOneNote.Main import *
"""
with open("C:\\Users\\george\\AppData\\Local\\Microsoft\\OneNote\\16.0\\备份\\财新网（存档）\\2022达沃斯论坛.one (于 2024-4-5).one", "rb") as file:
    valid = process_onenote_file(
        file = file,
        output_dir = "C:\\onenote_testfile",
        extension = "txt",
        json_output = True)
"""
def run_main():
    # 创建参数对象
    """
    参数说明
    p.add_argument("-f", "--file", action="store", help="File to analyze", required=True)
    p.add_argument("-o", "--output-dir", action="store", default="./", help="Path where store extracted files")
    p.add_argument("-e", "--extension", action="store", default="", help="Append this extension to extracted file(s)")
    p.add_argument("-j", "--json", action="store_true", default=False, help="Generate JSON output only, no dumps or prints")

    """
    args = argparse.Namespace(
        file="C:\\Users\\george\\AppData\\Local\\Microsoft\\OneNote\\16.0\\备份\\财新网（存档）\\2022达沃斯论坛.one (于 2024-4-5).one",
        output_dir="C:\\onenote_testfile",
        extension="txt",
        json=True
    )

    # 检查文件是否存在
    if not os.path.exists(args.file):
        sys.exit(f"File: {args.file} doesn't exist")

    # 打开文件并调用process_onenote_file
    with open(args.file, "rb") as file:
        process_onenote_file(file, args.output_dir, args.extension, args.json)

if __name__ == "__main__":
    run_main()

