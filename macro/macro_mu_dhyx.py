import pyautogui
import keyboard
import time

def click_mouse():
    while True:
        pyautogui.click()  # 模拟鼠标左键点击
        time.sleep(5)  # 每隔5秒点击一次

# 当按下'ctrl + shift + s'时，开始点击鼠标
keyboard.add_hotkey('ctrl + alt + a', click_mouse)

# 当按下'ctrl + shift + e'时，程序结束
keyboard.add_hotkey('ctrl + shift + e', exit)

# 保持程序运行
keyboard.wait()