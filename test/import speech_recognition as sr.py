import speech_recognition as sr

def listen_and_count():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    count = 0

    print("开始监听...")

    while True:
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source)
            print("请说话...")
            audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio, language='zh-CN')
            print(f"你说了: {text}")
            if "阿弥陀佛" in text:
                count += 1
                print(f"计数器: {count}")
        except sr.UnknownValueError:
            print("无法识别音频")
        except sr.RequestError as e:
            print(f"无法请求结果; {e}")

if __name__ == "__main__":
    listen_and_count()