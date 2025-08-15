import base64
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Part
import vertexai.preview.generative_models as generative_models

def generate():
    vertexai.init(project="just-lore-408313", location="us-central1")
    model = GenerativeModel("gemini-1.0-pro-vision-001")
    
    # Load image from folder
    with open(".\\ui\\2333854_1678116971.jpg", "rb") as image_file:
        image_data = image_file.read()
    
    # Convert image to base64
    #image_base64 = Part.from_data(data=base64.b64decode(base64.b64encode(image_data).decode("utf-8")), mime_type="image/jpeg")
    image_base64 = Part.from_data(data=image_data, mime_type="image/jpeg")
    responses = model.generate_content(
        [image_base64, """请告诉我这张图片是什么？是哪家公司的什么机型？"""],
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

#image1 = Part.from_data(data=base64.b64decode(""""""), mime_type="image/jpeg")

generate()