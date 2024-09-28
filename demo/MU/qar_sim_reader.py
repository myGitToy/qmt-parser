"""
读取研发中心提供的模拟机数据文档
csv格式 6HZ
"""
import csv
import re
import datetime
import pytz
import pandas as pd
# 显示所有的列
pd.set_option('display.max_columns', None)
class csv_reader():
    def __init__(self, file_path=None) -> None:
        """
        类初始化
        """
        

        self.file_path = file_path  #文件路径
        self.row_start = 1
        self.row_end = 20140
        # 增加一个参数词典，定义的参数有：
        self.param_dict = {
            "TIMESTAMP": "RECORDINGTIMESTAMP",  #'RECORDINGTIMESTAMP'
            "IAS": "CI99_POS_IAS_F4",   #空速
            "ALT": "G04_EOM_ALT_MSL_F8",    #高度
            "N1": "G71_N1P_F4[0]",  #发动机N1
            "HDG": "CG99_POS_UPRTPFD_MAGHEADING_F4",    #磁航向角
            "ROLL": "CG99_POS_UPRTPFD_ROLL_F4",  #滚转角
            "PITCH": "CG99_POS_UPRTPFD_PITCH_F4",   #俯仰角
            "AIL_FORCE": "CG99_POS_UPRTSYN_AILFORCE_F4", #副翼杆力
            "AIL_POS": "CG99_POS_UPRTSYN_AILPOSPCT_F4", #副翼位置
            "ELV_FORCE": "CG99_POS_UPRTSYN_ELVFORCE_F4", #升降舵杆力
            "ELV_POS": "CG99_POS_UPRTSYN_ELVPOSPCT_F4", #升降舵位置
            "RUD_FORCE": "CG99_POS_UPRTSYN_RUDFORCE_F4",    #方向舵杆力
            "AP": "CG99_POS_UPRTSYN_APENAGED_L1",   #自动驾驶仪接通状态
            "LOAD": "G04_EOM_NZ_F8",  #载荷
            "STAB_TRIM": "L99A_GEN_STAB_IND_F4[0]",  #配平位置
            "VS": "L99A_GEN_PFD_VERTSPEED_F4[0]"    #垂直速度
        }

        


        #self.column_list = ['RECORDINGTIMESTAMP', 'G22_AP_ENG_L1[0]', 'G04_EOM_ALT_MSL_F8','CG99_POS_UPRTSYN_PITCHTRIMACT_L1','G04_EOM_UG_F8','CI99_POS_IAS_F4','G04_TRIM_STATE_I4']
        self.column_list = list(self.param_dict.values())
        
        self.file_df = pd.DataFrame()

        # 数据校验
        if self.file_path is None:
            raise ValueError("文件路径不能为空")

        # 读取CSV文件并解析
        self.file_df = self.read_csv()

    def read_csv(self):
        """
        读取csv格式的文件并转换成dataframe格式
        由于文件过于庞大，因此需要指定
        """
        #df = pd.read_csv(self.file_path, skiprows=range(1, self.row_start), nrows=self.row_end-self.row_start, usecols=self.column_list)
        df = pd.read_csv(self.file_path,usecols=self.column_list)
        return df

    def data_process(self):
        """
        数据处理
        """
        ##### 时间戳的处理 #####
        # 保留原始时间戳用于定位
        self.file_df['ORIGINAL_TIMESTAMP'] = self.file_df['RECORDINGTIMESTAMP']
        #ORIGINAL_TIMESTAMP用于定位，放在第一列
        self.file_df = self.file_df[['ORIGINAL_TIMESTAMP'] + [col for col in self.file_df.columns if col != 'ORIGINAL_TIMESTAMP']]
        # 时间戳转换(单位为ms，转换为s，显示为hh:mm:ss.000）
        self.file_df['RECORDINGTIMESTAMP'] = self.file_df['RECORDINGTIMESTAMP'] / 10000
        self.file_df['RECORDINGTIMESTAMP'] = pd.to_datetime(self.file_df['RECORDINGTIMESTAMP'], unit='s').dt.strftime('%hh:%mm:%SS.%f')[:-3]
        #self.file_df['RECORDINGTIMESTAMP'] = pd.to_datetime(self.file_df['RECORDINGTIMESTAMP'], unit='s')
        print(self.file_df)
        # 丢弃最后三行数据
        self.file_df = self.file_df.drop(self.file_df.tail(3).index)
        # 数据按照RECORDINGTIMESTAMP重采样到秒，取平均值
        self.file_df =        self.file_df.set_index('RECORDINGTIMESTAMP').resample('S').mean().reset_index()
        #重采样后以时 分 秒显示
        #self.file_df['RECORDINGTIMESTAMP'] = self.file_df['RECORDINGTIMESTAMP'].dt.strftime('%H:%M:%S')
        
        #print(self.file_df['RECORDINGTIMESTAMP'])
        
        ######列格式转换#######
        # 高度数据 G04_EOM_ALT_MSL_F8 转换成整数英尺单位
        #self.file_df['G04_EOM_ALT_MSL_F8'] = self.file_df['G04_EOM_ALT_MSL_F8'].astype(int)
        #删除20000英尺以下的数据
        self.file_df = self.file_df[self.file_df['G04_EOM_ALT_MSL_F8'] > 20000] 


                
        #打印数据 
        print(self.file_df)      
        #显示RECORDINGTIMESTAMP为NaN的行
        #print(self.file_df[self.file_df['RECORDINGTIMESTAMP'].isnull()])
        # 显示CG99_POS_UPRTSYN_PITCHTRIMACT_L1 为True的情况
        #print(self.file_df[self.file_df['CG99_POS_UPRTSYN_PITCHTRIMACT_L1'] == True])
        # 显示G04_TRIM_STATE_I4一共出现几个数值
        print(self.file_df['G04_EOM_NZ_F8'].value_counts())


        ######循环file_df中的列名，如果列名在param_dict的值中，则将列名替换为param_dict的键
        reverse_param_dict = {v: k for k, v in self.param_dict.items()}
        for col in self.file_df.columns:   
            if col in reverse_param_dict.keys():
                self.file_df.rename(columns={col: reverse_param_dict[col]}, inplace=True)

        #####计算的列（需要放在此处，因为这里才是调用字典后的列名）######
        # 杆量的计算 column_pos_calc（计算公式为：if ELV_POS为正 则 ELV_POS/100 * 14.75；if ELV_POS为负 则 ELV_POS/100 * 13.75）
        self.file_df['column_pos_calc'] = self.file_df['ELV_POS'].apply(lambda x: x/100 * 14.75 if x > 0 else x/100 * 13.75)
        # 杆量column_pos_calc的列放在ELV_POS列后面
        
        # 盘量的计算 AIL_POS_calc 



# 使用示例
file_path = 'C:\\Log\\07Sep24-22h54m05s-.csv'
reader = csv_reader(file_path)
reader.data_process()
#数据存盘，文件名为当前日期+时间，包含索引
reader.file_df.to_csv('C:\\Log\\log' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.csv', index=True)


