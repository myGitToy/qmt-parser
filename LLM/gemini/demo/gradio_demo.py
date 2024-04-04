"""
测试vertexAI和Gradio结合的API接口
需要提前安装gcloud CLI，参考地址如下：
https://cloud.google.com/sdk/docs/install?hl=zh-cn
"""

import gradio as gr
import markdown
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Part
import vertexai.preview.generative_models as generative_models

def generate():
    pass

def process_input(text, file):
    vertexai.init(project="just-lore-408313", location="us-central1")
    model = GenerativeModel("gemini-1.0-pro-vision-001")
    responses = model.generate_content(
    f"""
    {text}
    """,
    generation_config={{
        "max_output_tokens": 2048,
        "temperature": 0.4,
        "top_p": 1,
        "top_k": 32
    }},
    safety_settings={{
        generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }},
    stream=False,
    )
    result = f"{markdown.markdown(responses.text)}"
    return result
def post_process_output(output):
    # Post-process the output here
    processed_output = f"Processed Output: {output}"
    return processed_output



iface1 = gr.Interface(fn=process_input, 
                inputs=["text", "file"], 
                outputs=["markdown"],
                #outputs=gr.outputs.Markdown(),
                title="Demo Page",
                description="A demo page with text input, file selection, and result text box")

iface2 = gr.Interface(
    fn=process_input, 
    inputs="image", 
    outputs="text",
    title="图片识别",
)

iface3 = gr.Interface(
    fn=process_input, 
    inputs="file", 
    outputs="text",
    title="文档总结",
)

#net = gr.Network([iface1, iface2, iface3])
iface1.post_process = post_process_output
iface1.launch()

