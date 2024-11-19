"""
构建一个QAR参数分析系统，目标是导入16HZ的分析参数，进行格式转换和时间序列分析
导入csv格式中的这两个参数，列名就是对应的中文名，但是Time是1HZ采样频率，因此csv中仅有1列，但是着陆载荷VRTG是16HZ采样频率，因此csv中仅有16列
"""
import csv
import re
import pytz
import pandas as pd
import re
import pytz
import chardet
import re
import pytz
import chardet
class ExcelReader():
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = {}
        # 定义参数的中文名、英文名、采样频率和单位
        self.parameters = {
            #其中时间列也被定义为基准列（1HZ->16HZ）
            "时间": {
                "英文名": "Time",
                "采样频率": "1HZ",
                "单位": ""
            },
            "QNH": {
                "英文名": "ALT_QNH",
                "采样频率": "1HZ",
                "单位": "feet"
            },
            "着陆载荷": {
                "英文名": "VRTG",
                "采样频率": "16HZ",
                "单位": "g"
            }
        }
        self.File_OG = None
        self.File = self.read_excel()
        
        self.columns = None

    def read_columns(self, column_name) ->pd.DataFrame:
        """
        读取file中指定列名的数据
        column_name: 列名的字典参数（每次均读取2列，其中强制读取Time列，作为基准）
        :return: 指定列名的数据
        """
        #如果self.parameters[column_name]['采样频率']为1HZ，则返回[column_name]['英文名']的列数据
        if column_name['采样频率'] == "1HZ":
            # 从file中提取指定列的数据
            df = self.File_OG[[self.parameters['时间']['英文名'], column_name['英文名']]]
            print("提取到的数据：")
            print(df)
            return df
        if column_name['采样频率'] == "16HZ":
            # 从file中提取指定列的数据
            # 16HZ数据列格式如下（以VRTG为例）  'VRTG', 'VRTG.1', 'VRTG.2', 'VRTG.3', 'VRTG.4', 'VRTG.5', 'VRTG.6', 'VRTG.7', 'VRTG.8', 'VRTG.9', 'VRTG.10', 'VRTG.11', 'VRTG.12', 'VRTG.13', 'VRTG.14', 'VRTG.15'
            # 因此输出VTRG+剩余15列的数据

            #读取输入的列名
            # multi_columns为参数列（根据HZ决定有几列）
            multi_columns = [column_name['英文名']] + [f"{column_name['英文名']}.{i}" for i in range(1, 16)]
            missing_columns = [col for col in multi_columns if col not in self.File_OG.columns]
            #列名校验
            if missing_columns:
                raise KeyError(f"列 '{', '.join(missing_columns)}' 不存在于Excel文件中")
            # 增加基准列 
            # base_columns的定义为Time列+参数列（根据HZ决定有几列）
            base_columns = [self.parameters['时间']['英文名']] + multi_columns
            df = self.File_OG[base_columns]
            print("提取到的数据：")
            print(df)
            #df转换成1/16秒的数据
            #举例：Time   VRTG VRTG.1 VRTG.2  ... VRTG.12 VRTG.13 VRTG.14 VRTG.15
            #转换后的列为Time   VRTG 
            #Time变成1/16秒的数据
            # 将Time列转换为1/16秒的数据
            # 将VRTG VRTG.1 VRTG.2  ... VRTG.12 VRTG.13 VRTG.14 VRTG.15由列转换成行
            df['Time'] = pd.to_datetime(df['Time'].apply(lambda x: x.strftime('%H:%M:%S')))
            df = df.melt(id_vars=['Time'], value_vars=multi_columns, var_name='VRTG', value_name='Value')
            print("转换后的数据：")
            print(df)   
            # 重采样成1/16秒的数据
            df['Time'] = pd.to_datetime(df['Time']) + pd.to_timedelta(df.groupby(df.index // 16).cumcount() * (1/16), unit='s')
            df = df[['Time', 'VRTG', 'Value']]

            print("转换后的数据：")
            print(df)

            return df
        
        if isinstance(column_name, str):
            column_name = [column_name]

        if not all(col in self.data.keys() for col in column_name):
            raise KeyError("指定的列名不存在")

        return pd.DataFrame({col: self.data[col] for col in column_name})

    def read_excel(self):
        try:
            # 读取Excel文件的全部行，其中第一行是字段名称，第二行是单位，第三行开始是数据
            df = pd.read_excel(self.file_path, header=[0])
            # 删除第一行数据（定义为单位的行）
            df = df.drop([0], axis=0)
            print("原始数据：")
            print(df)
            self.File_OG = df
            # 将提取到的原始列名存储到self.columns中
            self.columns = df.columns.tolist()
            print("列名:", self.columns)
            
            #提取QNH列
            self.read_columns(self.parameters['着陆载荷'])


            # 提取时间列
            time_column = self.parameters["时间"]["英文名"]
            if time_column not in df.columns:
                raise KeyError(f"列 '{time_column}' 不存在于Excel文件中")
            time_data = df[time_column]
            print("时间数据：")
            print(time_data)
            

            # 提取VRTG列
            vrtg_columns = [f"{self.parameters['着陆载荷']['英文名']}.{i}" for i in range(16)]
            missing_columns = [col for col in vrtg_columns if col not in df.columns]
            if missing_columns:
                raise KeyError(f"列 '{', '.join(missing_columns)}' 不存在于Excel文件中")
            vrtg_data = df[vrtg_columns]
            print("VRTG数据：")
            print(vrtg_data)
            
            # 展平VRTG数据并调整时间列
            vrtg_flattened = vrtg_data.values.flatten()
            time_repeated = time_data.repeat(16).reset_index(drop=True)
            time_adjusted = pd.to_datetime(time_repeated) + pd.to_timedelta((time_repeated.index % 16) * 62.5, unit='ms')
            
            # 创建新的DataFrame
            df_flattened = pd.DataFrame({
                time_column: time_adjusted,
                'VRTG': vrtg_flattened
            })
            
            print("展平后的数据：")
            print(df_flattened)
            
            # 存储数据
            self.data['时间'] = df_flattened[time_column]
            self.data['着陆载荷'] = df_flattened['VRTG']

        except pd.errors.ParserError as e:
            print(f"读取Excel文件出错: {e}")
        except KeyError as e:
            print(f"KeyError: {e}")

    def get_data(self):
        return self.data

            
            

# 使用示例
file_path = 'C:\\Log\\High vertical acceleration on ground ( Hard Landing)#B-7397_20240910_CSH9558.xlsx'
reader = ExcelReader(file_path)
file = reader.read_excel()