import akshare as ak
import pandas as pd
import gradio as gr
from datetime import datetime
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

    def get_concept(self, code: str = None) -> pd.DataFrame:
        """
        获取同花顺概念
        输入：
            code 证券代码（如果不输入，从self.code中获取）
        返回格式：
            code	concept_thscode	concept_name
            300001.SZ	886079.TI	2024中报预增
            300001.SZ	885690.TI	PPP概念
            300001.SZ	885921.TI	储能
        """
        if code is None:
            code = self.code
        return pd.read_sql(f"SELECT dtl.code,dtl.concept_thscode,idx.concept_name from stock_board_ths_concept_index as idx,stock_board_ths_concept_detail as dtl where idx.concept_thscode = dtl.concept_thscode and dtl.`code`='{code}'", con = self.engine)
    
    def get_industry_data_api(self, symbol: str = '汽车整车', start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        获取同花顺行业板块的每日行情数据（akshare api接口）
        盘中可以获取当天的实时数据
        输入：
            symbol 板块名称(如：汽车整车)
            start_date 开始日期 YYYYMMDD（如果不输入，从start_date中获取）
            end_date 结束日期 YYYYMMDD（如果不输入，从self.end_date中获取）
        返回格式：
            date	open	close	high	low	volume	amount	change_pct
            2024-01-02	0.0	0.0	0.0	0.0	0.0	0.0	0.0
            2024-01-03	0.0	0.0	0.0	0.0	0.0	0.0	0.0
            2024-01-04	0.0	0.0	0.0	0.0	0.0	0.0	0.0
        """
        #输入参数的校验，时间类的数据格式为YYYYMMDD
        if start_date is None and self.start_date is not None:
            start_date = self.start_date.strftime('%Y%m%d')
        if end_date is None and self.end_date is not None:
            end_date = self.end_date.strftime('%Y%m%d')
        if start_date is None and self.start_date is None:
            raise ValueError('请输入正确的时间参数') 
        if end_date is None and  self.end_date is None:
            raise ValueError('请输入正确的时间参数')   
        #如果start_date格式为datetime，转换成字符串
        if start_date is not None and isinstance(start_date,datetime):
            start_date = start_date.strftime('%Y%m%d')
        if end_date is not None and isinstance(end_date,datetime):
            end_date = end_date.strftime('%Y%m%d')
        #校验symbol所对应的行业板块代码 
        industry_thscode = self.get_industry_code(symbol) 
        if industry_thscode is None:
            raise ValueError('请输入正确的行业板块名称')
        #------数据校验结束 进入业务环节------
        #获取数据
        df = ak.stock_board_industry_index_ths(symbol = symbol , start_date = start_date , end_date = end_date)
        #数据列名称变更
        df.rename(columns = {'日期':'date','开盘价':'open','收盘价':'close','最高价':'high','最低价':'low','成交量':'volume','成交额':'money'},inplace = True)
        #df增加industry_thscode列
        df['industry_thscode'] = industry_thscode
        return df[['industry_thscode','date','open','close','high','low','volume','money',]]

    def get_industry_code(self, symbol: str = '汽车整车') -> str:
        """
        获取同花顺行业板块的代码(mysql数据库)
        输入：
            symbol 板块名称(如：汽车整车)
        返回格式：
            industry_thscode
        """
        #返回行业板块代码（dataframe中industry_thscode列第一行数据，如无返回None）
        industry_thscode_df = pd.read_sql(f"SELECT industry_thscode from stock_board_industry_name_ths where name = '{symbol}'", con = self.engine)
        industry_thscode = industry_thscode_df.iloc[0]['industry_thscode'] if not industry_thscode_df.empty else None
        return industry_thscode

    def update_industry_name(self):
        """
        更新同花顺行业板块入库
        返回格式：
            name    code
            半导体  881121
            白酒  881273
            白色家电  881131
        """
        #获取同花顺行业板块的全貌
        df_ths = ak.stock_board_industry_name_ths()
        #code列重命名
        df_ths.rename(columns = {'code':'industry_thscode'},inplace = True)
        #获取数据库中的数据
        df_db = pd.read_sql('select name,industry_thscode from stock_board_industry_name_ths',con = self.engine)
        #数据校验
        df_ths['industry_thscode'] = df_ths['industry_thscode'].astype(str)
        df_db['industry_thscode'] = df_db['industry_thscode'].astype(str)
        #差集校验
        df_diff = pd.concat([df_ths,df_db]).drop_duplicates(subset = ['industry_thscode'] , keep=False)
        df_diff.to_sql(
                name = 'stock_board_industry_name_ths',
                con = self.engine,
                index = False,
                if_exists = 'append')

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

    def update_concept_index(self , file_obj: gr.File) -> str:
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

    def update_concept_detail(self , file_obj: gr.File) -> str:
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
    t.code = '300002.SZ'
    t.start_date = datetime(2024,8,1)
    t.end_date  = datetime.now()
    print(t.get_industry_code('汽车整车2'))

    print(t.get_industry_data_api(symbol = '汽车整车'))
    #更新同花顺行业板块全貌
    t.update_industry_name()
    #同花顺板块的每日行情数据（非同花顺概念）
    #df_ths = ak.stock_board_industry_index_ths(symbol="汽车整车",start_date="20200101",end_date="20240807")
    #df_ths_name = ak.stock_board_industry_name_ths()
    df_ths_info_ths = ak.stock_board_industry_info_ths(symbol="汽车整车")
    print(df_ths_info_ths)
    print(df_ths_name)
    print(df_ths)
    df = t.get_concept()
    print(df)
    t.launch_gradio_interface()

