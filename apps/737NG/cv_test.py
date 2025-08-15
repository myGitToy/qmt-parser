import pandas as pd
import numpy as np
import cv2
import pytesseract
import matplotlib.pyplot as plt

# 读取CSV数据
data = pd.read_csv('C:\\Users\\george\\Desktop\\B-5461_20240830_CSH9331.csv',skiprows=5, header=0)

# 加载仪表板图像
img = cv2.imread('c:\\Primary_Flight_Display_of_a_Boeing_737-800.png')

# 定义函数，将数据填充到图像上
def update_image(img, data):
    # ... 具体填充逻辑，根据仪表盘布局和数据格式确定
    # 例如：
    # 使用OpenCV的putText函数将数值显示在指定位置
    #cv2.putText(img, str(data['airspeed']), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(img, str(234), (18, 370), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
def replace_text_in_image(img, search_text, replace_text):
    # 将图像转换为灰度图像
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 使用Tesseract进行OCR识别
    d = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
    
    n_boxes = len(d['level'])
    for i in range(n_boxes):
        if search_text in d['text'][i]:
            (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
            # 用白色矩形覆盖原文本
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 255, 255), -1)
            # 在原位置写入新文本
            cv2.putText(img, replace_text, (x, y + h - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

# 实时更新
for index, row in data.iterrows():
    # 更新图像
    update_image(img, row)

    # 显示图像
    cv2.imshow('Instrument Panel', img)

    # 等待按键，按下q退出
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()