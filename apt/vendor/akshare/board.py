import akshare as ak
import pandas as pd
import gradio as gr
from apt.vendor.akshare.data import data as akdata

class board(akdata):
    """
    专门处理板块数据的类
    """

class ths(board):
    """
    专门处理同花顺概念股的类，为板块的子类
    """
    def __init__(self):
        #使用super继承上级
        super(board , self).__init__()

    def launch_gradio_interface(self):
        """
        gradio接口，用于处理数据更新
        """
        # 使用 gradio 的新 API
        with gr.Blocks() as demo:
            with gr.Row():
                with gr.Column(scale=1):
                    #同花顺指数概念 左侧1/2
                    #文件上传框
                    concept_file_input = gr.File(label="上传同花顺指数文件（133kb）")
                    #提交框
                    concept_submit_button = gr.Button("提交", size="small")
                    # 输出框
                    concept_output = gr.Textbox(label="输出结果")
                with gr.Column(scale=1):
                    #同花顺代码概念  右侧1/2
                    code_file_input = gr.File(label="上传同花顺代码文件 (2MB)")
                    #提交框
                    code_submit_button = gr.Button("提交", size="small")
                    # 输出框
                    code_output = gr.Textbox(label="输出结果")
            #点击事件
            concept_submit_button.click(fn=self.update_concept_index , inputs=concept_file_input , outputs=concept_output)
            code_submit_button.click(fn=self.update_concept_detail , inputs=code_file_input , outputs=code_output)
            #运行
            demo.launch()

    def update_concept_index(self , file_obj):
        """
        读取同花顺概念指数的csv文件并导入数据库[stock_board_ths_concept_index]
        file_obj: gradio传入的文件对象
        必须配合gradio使用
        """
        # 从 Gradio 文件组件中提取文件路径
        file_path = file_obj.name
        #读取csv文件
        df_csv = pd.read_csv(file_path)
        #数据校验，必须包含concept_name	concept_symbol两列
        if 'concept_name' not in df_csv.columns or 'concept_symbol' not in df_csv.columns:
            return ValueError('非法的数据结构，请检查文件')
        #数据有效，与数据库中的数据进行去重后导入
        df_db = pd.read_sql('select * from stock_board_ths_concept_index',con = self.engine)
        # 确保 concept_symbol 列的数据类型一致
        df_csv['concept_symbol'] = df_csv['concept_symbol'].astype(str)
        df_db['concept_symbol'] = df_db['concept_symbol'].astype(str)
        df_diff = pd.concat([df_csv,df_db]).drop_duplicates(subset = ['concept_symbol'] , keep=False)
        if df_diff.empty == True:
            return("数据无更新")
        else:
            df_diff.to_sql(
                    name = f'stock_board_ths_concept_index',
                    con = self.engine,
                    index = False,
                    if_exists = 'append')
            return(f"{df_diff.shape[0]}条差异数据已上传")

    def update_concept_detail(self , file_obj):
        """
        读取同花顺概念代码的csv文件并导入数据库[stock_board_ths_concept_detail]
        file_obj: gradio传入的文件对象
        必须配合gradio使用
        """
        # 从 Gradio 文件组件中提取文件路径
        file_path = file_obj.name
        #读取csv文件
        df_csv = pd.read_csv(file_path, usecols = ['code',  'concept_thscode'])
        #数据校验，必须包含concept_name	concept_symbol两列
        if 'code' not in df_csv.columns or 'concept_thscode' not in df_csv.columns:
            return ValueError('非法的数据结构，请检查文件')
        #数据有效，与数据库中的数据进行去重后导入
        df_db = pd.read_sql('select code,concept_thscode from stock_board_ths_concept_detail' , con = self.engine)
        # 确保 concept_symbol 列的数据类型一致
        df_csv['code'] = df_csv['code'].astype(str)
        df_csv['concept_thscode'] = df_csv['concept_thscode'].astype(str)
        df_db['code'] = df_db['code'].astype(str)
        df_db['concept_thscode'] = df_db['concept_thscode'].astype(str)       
        df_diff = pd.concat([df_csv,df_db]).drop_duplicates(subset = ['code','concept_thscode'] , keep = False)
        #print(df_diff)
        if df_diff.empty == True:
            return("数据无更新")
        else:
            df_diff.to_sql(
                    name = f'stock_board_ths_concept_detail',
                    con = self.engine,
                    index = False,
                    if_exists = 'append')
            return(f"{df_diff.shape[0]}条差异数据已上传")

class ths_old(board):
    """
    专门处理同花顺概念股的类，为板块的子类
    akdata->board->ths
    同花顺概念数据分为四个层级：
        #第一层 更新概念时间表 接口: stock_board_concept_name_ths
        #第二层 更新概念股票列表 接口: stock_board_concept_cons_ths
        #第三层 更新概念股票信息 接口: stock_board_concept_detail_ths
        #第四层 更新概念股票历史信息 接口: stock_board_concept_detail_hist_ths
    ---> (1.14以后相关接口被移除)
    https://github.com/akfamily/akshare/issues/5018
    """
    def __init__(self):
        #使用super继承上级
        super(board , self).__init__()
        raise ValueError('ths_old已经被移除，请使用ths')
    def get_layer1_同花顺概念时间表(self):
        """
        第一层 更新概念时间表 接口: stock_board_concept_name_ths
        """
        return ak.stock_board_industry_summary_ths()
    
if __name__ == "__main__":
    t = ths()
    t.launch_gradio_interface()

