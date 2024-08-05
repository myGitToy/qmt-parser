"""
使用gradio完成一个简单的google gemini 对话的demo
"""
import gradio as gr

def gemini_demo(question):
    # 这里只是一个示例函数，实际应用中应该是调用Google Gemini API并返回结果
    answers = {
        "你好": "你好！很高兴见到你。",
        "你是谁": "我是一个由Gradio驱动的简单Google Gemini对话演示。",
    }
    return answers.get(question, "抱歉，我不明白你的问题。")

iface = gr.Interface(fn=gemini_demo, 
                     inputs=gr.inputs.Textbox(lines=2, placeholder="请输入你的问题..."), 
                     outputs="text",
                     title="Google Gemini 对话演示",
                     description="输入一个问题，看看我怎么回答。")

if __name__ == "__main__":
    iface.launch()