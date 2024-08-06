import akshare as ak
import pandas as pd
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

    def update_concept(self , file_path = None):
        """
        读取同花顺概念指数的csv文件并导入数据库
        配合gradio使用
        """
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
    t = ths_old()
    t = ak.get_layer1_同花顺概念时间表()
    print(df)
    #csv数据存盘
    df.to_csv('/data/stock_board_concept_detail_hist_ths.csv', encoding='utf-8-sig')
    #导入概念指数
    df_concept = get_concept_relate(date = '20250806')
    print(df_concept)
    df_concept.to_csv('ths_concept.csv',index=False)
    #循环的导入概念指数中的全部成分股
    df_all = pd.DataFrame()
    """
    df_concept数据结构如下： 
    concept_name为index
    其余列：concept_symbol concept_code concept_level concept_levelname concept_rank concept_thscode available_date disabled_date
    """
    #历遍df_concept，取出所有concept_thscode不为空的数据，然后调用get_concept_stock(concept_thscode_name)
    for index, row in df_concept.iterrows():
        if row['concept_thscode'] != None:
            print(row['concept_thsc ode'])
            code_list = get_concept_stocks(row['concept_thscode'])
            # 返回的code_list为列表，如果为空，则不进行处理，如果不为空，则将其转换为DataFrame，然后进行拼接
            if len(code_list) > 0:
                df = pd.DataFrame(code_list, columns=["code"])
                print(df_concept.columns)
                df["concept_name"] = index
                df["concept_thscode"] = row["concept_thscode"]
                print(f'{index} 已处理完成')
                # df_all = pd.concat([df_all,df])
