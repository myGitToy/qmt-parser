"""
测试文件读取模块
"""
from agent.document_loader.mydocloader import RapidOCRDocLoader
from agent.document_loader.mypdfloader import RapidOCRPDFLoader


"""
#docx读取测试：自动读取文档的分块数据，如果有图片则会进行OCR识别
返回格式
[Document(page_content='XXXX', metadata={'source': 'C:\\Users\\xxxx.docx'})]
"""
#docx_loader = RapidOCRDocLoader(file_path="C:\\Users\\george\\OneDrive\\文稿\\2024党员民主评议-自我总结.docx")
#docs = docx_loader.load()
#print(docs)

"""
#pdf读取测试：自动读取文档的分块数据，如果有图片则会进行OCR识别
返回格式
[Document(page_content='XXXX', metadata={'source': 'C:\\Users\\xxxx.docx'})]
"""
pdf_loader =  RapidOCRPDFLoader(file_path="C:\\Users\\george\\OneDrive\\Desktop\\南航大报名\\课程\\自然辩证法概论\\自然辩证法概论  修订版.pdf")
pdfs = pdf_loader.load()
print(pdfs)