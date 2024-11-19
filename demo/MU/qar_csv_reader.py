"""
构建一个QAR参数分析系统，目标是导入16HZ的分析参数，进行格式转换和时间序列分析

构建一个csv文件对应的列和字段的对照表
首先定义读取的模板：
csv文件第一行格式如下：
A/C Type: B737-800   A/C Tail: B-5461   Flight No: CSH9331   From-To: ZSSS-ZGSZ   
对应为机型、机尾号 航班号 起降航段
csv文件第二行格式如下：
Selected Flight Date: 30/08/2024 02:18:42 - 30/08/2024 04:30:45   Frame: 1 - 1982   
对应分别为航班起飞时刻和落地时刻，世界时
csv文件第三行格式如下：
File No: 728750   Analyzed by AGS Db Version: 406   
对应为数据库编码 ，这里是406编码，其他的选项有407 409 411等

其他参数，如采样频率需要手动定义，分1HZ 2HZ 4HZ 8HZ 16HZ
"""
import csv
import re
import datetime
import pytz

class csv_reader():
    def __init__(self, file_path=None) -> None:
        """
        类初始化
        """
        self.file_path = file_path  
        self.data = {}

        # 数据校验
        if self.file_path is None:
            raise ValueError("文件路径不能为空")

        # 读取CSV文件并解析
        self.read_csv()

    def read_csv(self):
        with open(self.file_path, mode='r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            lines = [next(csv_reader) for _ in range(4)]  # 读取前4行

            # 解析第一行
            first_line = lines[1][0]
            self.data['机型'] = self.extract_value(first_line, r'A/C Type: (.*?)\s')
            print(self.data['机型'])
            self.data['机尾号'] = self.extract_value(first_line, r'A/C Tail: (.*?)\s')
            print(self.data['机尾号'])
            self.data['航班号'] = self.extract_value(first_line, r'Flight No: (.*?)\s')
            print(self.data['航班号'])
            self.data['起降航段'] = self.extract_value(first_line, r'From-To: (.*?)\s')
            print(self.data['起降航段'])

            # 解析第二行
            second_line = lines[2][0]
            #flight_times = second_line.split(' - ')
            start_time = self.extract_value(second_line, r'Selected Flight Date: (.*?)\s-\s')
            end_time = self.extract_value(second_line, r'-\s(.*?)\sFrame:')
            start_time = datetime.datetime.strptime(start_time, "%d/%m/%Y %H:%M:%S")
            end_time = datetime.datetime.strptime(end_time, "%d/%m/%Y %H:%M:%S")
            self.data['起飞时刻'] = start_time.strftime("%Y-%m-%d %H:%M:%S") + " UTC"
            self.data['落地时刻'] = end_time.strftime("%Y-%m-%d %H:%M:%S") + " UTC"
            # 解析第三行
            third_line = lines[3][0]
            self.data['数据库编码'] = self.extract_value(third_line, r'Analyzed by AGS Db Version: (.*?)\s')
            print(self.data['数据库编码'])
            pass
    def extract_value(self, text, pattern):
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
        return None

    def get_data(self):
        return self.data

# 使用示例
file_path = 'C:\\Log\\B-5461_20240830_CSH9331.csv'
reader = csv_reader(file_path)
data = reader.get_data()
print(data)