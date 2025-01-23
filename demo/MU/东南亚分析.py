import pandas as pd
import os
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']    # 使用中文字体
plt.rcParams['axes.unicode_minus'] = False      # 正常显示负号
"""
读取桌面目录下的“2025-01-23-13-23-56.csv"文件，找出航班日期，降落风速，着陆距离修正三列，按照月份进行箱体图绘制
"""
airport = 'VTBS'
def 数据读取():
    """
    按照指定的目录读取数据并且完成对应的数据清洗
    """    
    # 读取桌面目录下的“2025-01-23-14-38-51.csv"文件
    csv_file_path = os.path.join(os.path.expanduser('~'), 'Desktop', '2025-01-23-14-38-51.csv')
    # 尝试使用不同的编码格式读取文件
    try:
        csv_data = pd.read_csv(csv_file_path, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            csv_data = pd.read_csv(csv_file_path, encoding='gbk', low_memory=False)
        except UnicodeDecodeError:
            csv_data = pd.read_csv(csv_file_path, encoding='latin1')

    # 读取航班日期，降落风速，DIST_LANDING三列
    csv_data = csv_data[['航班日期','降落机场四字码', '降落风速','降落时间','DIST_LDG','ROLL_MAX_BL100','VRTG_MAX_LD','RETARD_ALT','PITCH_LANDING']]
    # 数据筛选，只保留降落机场四字码符合要求的数据
    csv_data = csv_data[csv_data['降落机场四字码'] == airport]

    ## 格式修正 
    # 将航班日期转换为日期格式  
    csv_data['航班日期'] = pd.to_datetime(csv_data['航班日期'])
    # 对降落时间进行修正，原格式为2023/1/23  14:26:00，时间为世界时，需要转换成北京时
    # 先将无效值或“-”替换为缺失值，去除空值后再转成datetime并转换时区
    # 删除降落时间为-的行
    csv_data = csv_data[csv_data['降落时间'] != '-']
    csv_data.dropna(subset=['降落时间'], inplace=True)
    # 时区转换
    csv_data['降落时间'] = pd.to_datetime(csv_data['降落时间'], utc=True).dt.tz_convert('Asia/Shanghai')
    
    
    # 新增是否通宵列，对于降落时间在北京时间00:00-8:00的均定义为通宵航班
    csv_data['是否通宵'] = csv_data['降落时间'].dt.hour.between(0, 7)  # 0~7 点视为通宵
    # 添加月份列
    csv_data['年月'] = csv_data['航班日期'].dt.strftime('%y.%m')
    # 将降落风速和DIST_LANDING转换为数值格式，无法转换的值替换为NaN
    csv_data['降落风速'] = pd.to_numeric(csv_data['降落风速'], errors='coerce')
    csv_data['DIST_LDG'] = pd.to_numeric(csv_data['DIST_LDG'], errors='coerce')
    csv_data['ROLL_MAX_BL100'] = pd.to_numeric(csv_data['ROLL_MAX_BL100'], errors='coerce')
    csv_data['VRTG_MAX_LD'] = pd.to_numeric(csv_data['VRTG_MAX_LD'], errors='coerce')        
    csv_data['RETARD_ALT'] = pd.to_numeric(csv_data['RETARD_ALT'], errors='coerce')
    csv_data['PITCH_LANDING'] = pd.to_numeric(csv_data['PITCH_LANDING'], errors='coerce')
    # 数据清洗DIST_LDG字段为0的数据删除，大于5000的也删除
    csv_data = csv_data[(csv_data['DIST_LDG'] != 0) & (csv_data['DIST_LDG'] < 5000)]
    # 数据清洗 剔除PITCH_LANDING>10的数据
    csv_data = csv_data[csv_data['PITCH_LANDING'] <= 10]
    # 对DIST_LDG进行修正，大于5000的值全部替换为2000
    # 输出csv_data['DIST_LDG'] 的分布情况
    print(csv_data['DIST_LDG'].describe())
    csv_data['DIST_LDG'] = csv_data['DIST_LDG'].apply(lambda x: 2000 if x > 5000 else x)
    return csv_data
    # 跳过非数值列，只针对数值列生成箱体图
    numeric_columns = [col for col in csv_data.columns if pd.api.types.is_numeric_dtype(csv_data[col])]

def 作图模块(csv_data  = None ,col = None , name = None):
    # 按照月份进行箱体图绘制，并叠加降落风速的折线图
    fig, ax1 = plt.subplots()

    # 绘制着陆距离修正的箱体图
    csv_data.boxplot(column=col, by='年月', grid=False, ax=ax1)
    ax1.set_title(f'{airport}|{name} 与季节性着陆风速关系箱体图')
    ax1.set_xlabel('月份')
    ax1.set_ylabel(name)
    #ax1.set_ylim(1800, 2500)  # Set y-axis limits
    plt.suptitle('')

    # 创建第二个y轴，绘制降落风速的折线图
    ax2 = ax1.twinx()
    monthly_wind_speed = csv_data.groupby('年月')['降落风速'].mean()
    ax2.plot(monthly_wind_speed.index, monthly_wind_speed.values, color='r', marker='o', linestyle='-', linewidth=2)
    ax2.set_ylabel('降落风速 米/秒', color='r')
    ax2.tick_params(axis='y', labelcolor='r')           
    # 设置相同的x轴刻度
    ax1.set_xticklabels(monthly_wind_speed.index, rotation=90)
    ax2.set_xticklabels(monthly_wind_speed.index, rotation=90)

    # 设置标题
    #plt.title(f'{airport}|{name} 与季节性着陆风速关系箱体图')

    # 保存图片
    plt.savefig(os.path.join('c:\\test', f'{airport} {name} 与季节性着陆风速关系箱体图.png'), dpi=300)
    plt.tight_layout()
    #plt.show()
    #input("按回车键退出...")

if __name__ == "__main__":
    # 定义需要循环出图的列,json格式，键为列名，值为图表名称
    col = { 'DIST_LDG': '着陆距离',
            'ROLL_MAX_BL100': '100英尺以下最大坡度',
            'VRTG_MAX_LD': '着陆载荷',
            'RETARD_ALT' : '油门杆收光高度',
            'PITCH_LANDING':'着陆姿态'}
    # 数据读取
    csv_data = 数据读取()
    print(csv_data)
    # 循环出图
    for column, name in col.items():
        作图模块(csv_data, column, name)
    
    # 


