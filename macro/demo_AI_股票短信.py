"""
At the command line, only need to run once to install the package via pip:

$ pip install google-generativeai
"""

import google.generativeai as genai

genai.configure(api_key="AIzaSyAwu9oo64mDBERyWZGB0hc1faB9izogP5w")

# Set up the model
generation_config = {
  "temperature": 0.9,
  "top_p": 1,
  "top_k": 1,
  "max_output_tokens": 2048,
}

safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
]

model = genai.GenerativeModel(model_name="gemini-1.0-pro",
                              generation_config=generation_config,
                              safety_settings=safety_settings)

prompt_parts = [
  "input: 【银河证券】《财富星私享-股赢尊享》：操作建议：当升科技（买入操作）：调入当升科技(300073)，建仓区间46.77元-47.25元，调入标的份额：1500股，止损价40.16元。调入理由：固态电池概念，目前股价回踩可以低吸。请您自行阅读创业板相关风险提示，了解各类交易标的特殊交易规则以及风险。投顾建议仅供参考，请您独立审慎作出投资决策。[回复TD017退订]",
  "output: {\"证券名称\": \"当升科技\", \"方向\": \"买入操作\",\"证券代码\":\"300073\",\"区间上限\":46.77,\"区间下限\":47.25,\"份额\":1500,\"止损价格\":40.16,\"调入理由\":\"固态电池概念，目前股价回踩可以低吸\"}",
  "input: 【银河证券】《财富星-股赢一号》：操作建议：川投能源（买入操作）：调入川投能源(600674)，建仓区间17.0元-17.18元，止损价15.0元。调入理由：低位大盘股，有望超跌反弹。风险提示：建议个股跟买仓位不超过总仓位的10%。本信息仅供参考，请您审慎决策。[回复TD008退订]",
  "output: ",
]

response = model.generate_content(prompt_parts)
print(response.text)