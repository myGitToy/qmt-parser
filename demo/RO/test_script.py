"""
仙境传说RO脚本翻译器，按行读取，遇到mes的行，翻译成中文
"""
import re
import os
import sys
import time
import argparse
import logging
import os
import time
import google.generativeai as genai

#genai.configure(api_key=os.environ["AIzaSyBArrGZSo3YMAp_K_2a4ab7LxCLohoD-ko"])
class google_gemini_translator():
    """
    按行调用gemini接口进行翻译，每次翻译传入一行+上下文+定义的System Instructions
    """
    def __init__(self, api_key):
        self.api_key = api_key

    def translate(self, text, context=""):
        # Create the model
        generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
        }

        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=generation_config,
            # safety_settings = Adjust safety settings
            # See https://ai.google.dev/gemini-api/docs/safety-settings
            system_instruction="请翻译脚本文件，mes为消息内容，需要翻译成中文，其余保留格式不变。另外mes中会有部分类似于^EE0000的内容，不需要翻译",
            )
    

class script_translator():
    def __init__(self, script_path=None, output_path=None) -> None:
        """
        类初始化
        """
        self.script_path = script_path
        self.output_path = output_path
        self.translated_script = ""
        self.translated_line = ""
        self.translated_lines = []
        self.mes_dict = {}
        self.mes_list = []
        self.mes = ""
        self.mes_id = ""
        self.mes_content = ""

    def translate_script(self):
        """
        读取脚本文件，按行翻译
        """
        with open(self.script_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                #print(line, end='')
                print(line, end='')
                """
                进行逻辑判断，需要翻译的情况有：
                    以//开头的行
                    以很多空格开头，接着含mes字样的行               
                """
                if line.startswith("//"):
                    print("注释行，需要翻译")
                    #self.translated_line = line
                elif re.match(r"^\s+mes", line):
                    print("需要翻译的行")
                    #self.mes = line
                    #self.mes_id = self.mes.split()[1]
                    #self.mes_content = self.mes.split()[2]
                    print(f"mes_id: {self.mes_id}, mes_content: {self.mes_content}")
                    #self.translated_line = self.translate_line(line)
                else:
                    print("不需要翻译的行")
                    #self.translated_line = line

                #self.translated_line = self.translate_line(line)
                #self.translated_lines.append(self.translated_line)
            #self.translated_script = "".join(self.translated_lines)
            #self.write_output()

if __name__ == "__main__":

    """
    parser = argparse.ArgumentParser(description="Translate RO script from English to Chinese.")
    parser.add_argument("script_path", help="Path to the script file.")
    parser.add_argument("output_path", help="Path to the output file.")
    args = parser.parse_args()
    translator = script_translator(args.script_path, args.output_path)
    translator.translate_script()    
    """
    parser = script_translator()
    parser.script_path = "C:\\Log\\izlude.txt"
    parser.output_path = "C:\\Log\\izlude_cn.txt"
    parser.translate_script()
