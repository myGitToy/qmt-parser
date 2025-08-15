import os
import google.generativeai as genai
from PyPDF2 import PdfReader
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from google.generativeai.types import HarmCategory, HarmBlockThreshold
# 设置API KEY
GOOGLE_API_KEY = 'AIzaSyAwu9oo64mDBERyWZGB0hc1faB9izogP5w' 
genai.configure(api_key=GOOGLE_API_KEY)

#设置模型
model = genai.GenerativeModel('models/gemini-1.5-pro-latest')

def select_file():
    Tk().withdraw()  # 隐藏主窗口
    filename = askopenfilename()  # 显示文件选择对话框
    return filename

def read_pdf(file_path):
    with open(file_path, 'rb') as file:
        reader = PdfReader(file)
        total_pages = len(reader.pages)
        text = ""
        for page in reader.pages:
            text = text + page.extract_text()
            
        return text

#设置问题及返回列表
def generate():
    """
    加载pdf文件，提取文本，然后生成文本
    """
    #获取pdf路径
    file_path = select_file()
    #获取pdf内容
    content_text = read_pdf(file_path)
    #附加内容
    #你是一位资深的财务顾问，请根据上述文档，给出这家公司的财务分析模型，请一步一步详细分析和解答。另外PDF文本中
    content_text = content_text + \
    """
    总结一下进行文本摘要，请用中文回答
    """
    response = model.generate_content(content_text ,
        generation_config={
        "max_output_tokens": 8192,
        "temperature": 0.7,
        "top_p": 1,
        "top_k": 1
        },
        safety_settings={
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    },
        stream=True,
    )
    for chunk in response:
        print(chunk.text)

generate()















"""

import pathlib
import textwrap
from IPython.display import display
from IPython.display import Markdown
def to_markdown(text):
    text = text.replace('•', '  *')
    return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

#设置AIP KEY
GOOGLE_API_KEY=userdata.get('AIzaSyAwu9oo64mDBERyWZGB0hc1faB9izogP5w')

genai.configure(api_key=GOOGLE_API_KEY)
genai.configure(api_key=os.environ['AIzaSyAwu9oo64mDBERyWZGB0hc1faB9izogP5w'])
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content("Write a cute story about cats.", stream=True)
for chunk in response:
  print(chunk.text)
  print("_"*80)
"""