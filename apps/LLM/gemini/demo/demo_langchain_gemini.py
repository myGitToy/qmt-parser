"""
https://python.langchain.com/v0.1/docs/integrations/chat/google_generative_ai/
using google generative ai
"""
import getpass
import os
from langchain_google_genai import ChatGoogleGenerativeAI

if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = "AIzaSyAwu9oo64mDBERyWZGB0hc1faB9izogP5w"
    #getpass.getpass("AIzaSyAwu9oo64mDBERyWZGB0hc1faB9izogP5w")
llm = ChatGoogleGenerativeAI(model="gemini-pro")
for chunk in llm.stream("我想要一份statble diffusion的提示词，我用中文来描述，请你用英文来输出，请补充关于光影 环境等细节性的描述和其他任何你认为有益于这张图片的内容，下面是我的描述：在一个阳光明媚的中午，沙滩上躺着一位漂亮美丽的女孩，手上拿着一份椰子饮料"):
    print(chunk.content)
    print("---")