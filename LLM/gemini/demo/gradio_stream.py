import gradio as gr
import random
import time
import vertexai
import vertexai.preview.generative_models as generative_models
from vertexai.preview.generative_models import GenerativeModel, Part
def generate(message):
    vertexai.init(project="just-lore-408313", location="us-central1")
    model = GenerativeModel("gemini-1.0-pro-vision-001")
    responses = model.generate_content(
        f"""
        {message}
        """,
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
        stream=False,
    )
    return responses.text
    for response in responses:
        print(response.text, end="")

def respond(message, chat_history):
    #调用gemini API
    bot_message = generate(message)
    chat_history.append((message, bot_message))
    btn_history.update()
    #time.sleep(2)
    return "", chat_history


with gr.Blocks() as demo:
    #初始化按钮
    btn_chatbot = gr.Chatbot()
    txt_msg = gr.Textbox()
    btn_clear = gr.ClearButton([txt_msg, btn_chatbot])
    btn_history = gr.Textbox()
    
    #调用默认的示例
    #msg.submit(respond, [msg, chatbot], [msg, chatbot])
    #调用gemini API
    txt_msg.submit(respond, [txt_msg, btn_chatbot], [txt_msg, btn_chatbot])
demo.launch()