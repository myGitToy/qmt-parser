"""
测试vertexAI的API接口
需要提前安装gcloud CLI，参考地址如下：
https://cloud.google.com/sdk/docs/install?hl=zh-cn
"""
from PyPDF2 import PdfReader
import vertexai
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from vertexai.preview.generative_models import GenerativeModel, Part
import vertexai.preview.generative_models as generative_models

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


def generate():
  """
  加载pdf文件，提取文本，然后生成文本
  """
  #获取pdf路径
  file_path = select_file()
  #获取pdf内容
  content_text = read_pdf(file_path)
  #附加内容
  content_text = content_text + \
  """
  机组资源管理又称为CRM，根据上述文本，你作为一名航空专家，请告诉我第五代CRM相对于第四代CRM最大的改变是什么？为什么会有这样的改变？
  """
  vertexai.init(project="just-lore-408313", location="us-central1")
  model = GenerativeModel("gemini-1.0-pro-vision-001")
  
  responses = model.generate_content(
    content_text,
    generation_config={
        "max_output_tokens": 2048,
        "temperature": 0.4,
        "top_p": 1,
        "top_k": 32
    },
    safety_settings={
        generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    },
    stream=True,
  )
  
  for response in responses:
    print(response.text, end="")

generate()