"""
财务指标数据
https://tushare.pro/document/2?doc_id=79
接口：fina_indicator，可以通过数据工具调试和查看数据。
描述：获取上市公司财务指标数据，为避免服务器压力，现阶段每次请求最多返回60条记录，可通过设置日期多次请求获取更多数据。
权限：用户需要至少2000积分才可以调取，具体请参阅积分获取办法
提示：当前接口只能按单只股票获取其历史数据，如果需要获取某一季度全部上市公司数据，请使用fina_indicator_vip接口（参数一致），需积攒5000积分。

参数如下：
ts_code	str	Y	TS代码
ann_date	str	Y	公告日期
end_date	str	Y	报告期
eps	float	Y	基本每股收益
dt_eps	float	Y	稀释每股收益
total_revenue_ps	float	Y	每股营业总收入
revenue_ps	float	Y	每股营业收入
capital_rese_ps	float	Y	每股资本公积
surplus_rese_ps	float	Y	每股盈余公积
undist_profit_ps	float	Y	每股未分配利润
extra_item	float	Y	非经常性损益
profit_dedt	float	Y	扣除非经常性损益后的净利润（扣非净利润）
gross_margin	float	Y	毛利
current_ratio	float	Y	流动比率
quick_ratio	float	Y	速动比率
cash_ratio	float	Y	保守速动比率
invturn_days	float	N	存货周转天数
arturn_days	float	N	应收账款周转天数
inv_turn	float	N	存货周转率
ar_turn	float	Y	应收账款周转率
ca_turn	float	Y	流动资产周转率
fa_turn	float	Y	固定资产周转率
assets_turn	float	Y	总资产周转率
op_income	float	Y	经营活动净收益
valuechange_income	float	N	价值变动净收益
interst_income	float	N	利息费用
daa	float	N	折旧与摊销
ebit	float	Y	息税前利润
ebitda	float	Y	息税折旧摊销前利润
fcff	float	Y	企业自由现金流量
fcfe	float	Y	股权自由现金流量
current_exint	float	Y	无息流动负债
noncurrent_exint	float	Y	无息非流动负债
interestdebt	float	Y	带息债务
netdebt	float	Y	净债务
tangible_asset	float	Y	有形资产
working_capital	float	Y	营运资金
networking_capital	float	Y	营运流动资本
invest_capital	float	Y	全部投入资本
retained_earnings	float	Y	留存收益
diluted2_eps	float	Y	期末摊薄每股收益
bps	float	Y	每股净资产
ocfps	float	Y	每股经营活动产生的现金流量净额
retainedps	float	Y	每股留存收益
cfps	float	Y	每股现金流量净额
ebit_ps	float	Y	每股息税前利润
fcff_ps	float	Y	每股企业自由现金流量
fcfe_ps	float	Y	每股股东自由现金流量
netprofit_margin	float	Y	销售净利率
grossprofit_margin	float	Y	销售毛利率
cogs_of_sales	float	Y	销售成本率
expense_of_sales	float	Y	销售期间费用率
profit_to_gr	float	Y	净利润/营业总收入
saleexp_to_gr	float	Y	销售费用/营业总收入
adminexp_of_gr	float	Y	管理费用/营业总收入
finaexp_of_gr	float	Y	财务费用/营业总收入
impai_ttm	float	Y	资产减值损失/营业总收入
gc_of_gr	float	Y	营业总成本/营业总收入
op_of_gr	float	Y	营业利润/营业总收入
ebit_of_gr	float	Y	息税前利润/营业总收入
roe	float	Y	净资产收益率
roe_waa	float	Y	加权平均净资产收益率
roe_dt	float	Y	净资产收益率(扣除非经常损益)
roa	float	Y	总资产报酬率
npta	float	Y	总资产净利润
roic	float	Y	投入资本回报率
roe_yearly	float	Y	年化净资产收益率
roa2_yearly	float	Y	年化总资产报酬率
roe_avg	float	N	平均净资产收益率(增发条件)
opincome_of_ebt	float	N	经营活动净收益/利润总额
investincome_of_ebt	float	N	价值变动净收益/利润总额
n_op_profit_of_ebt	float	N	营业外收支净额/利润总额
tax_to_ebt	float	N	所得税/利润总额
dtprofit_to_profit	float	N	扣除非经常损益后的净利润/净利润
salescash_to_or	float	N	销售商品提供劳务收到的现金/营业收入
ocf_to_or	float	N	经营活动产生的现金流量净额/营业收入
ocf_to_opincome	float	N	经营活动产生的现金流量净额/经营活动净收益
capitalized_to_da	float	N	资本支出/折旧和摊销
debt_to_assets	float	Y	资产负债率
assets_to_eqt	float	Y	权益乘数
dp_assets_to_eqt	float	Y	权益乘数(杜邦分析)
ca_to_assets	float	Y	流动资产/总资产
nca_to_assets	float	Y	非流动资产/总资产
tbassets_to_totalassets	float	Y	有形资产/总资产
int_to_talcap	float	Y	带息债务/全部投入资本
eqt_to_talcapital	float	Y	归属于母公司的股东权益/全部投入资本
currentdebt_to_debt	float	Y	流动负债/负债合计
longdeb_to_debt	float	Y	非流动负债/负债合计
ocf_to_shortdebt	float	Y	经营活动产生的现金流量净额/流动负债
debt_to_eqt	float	Y	产权比率
eqt_to_debt	float	Y	归属于母公司的股东权益/负债合计
eqt_to_interestdebt	float	Y	归属于母公司的股东权益/带息债务
tangibleasset_to_debt	float	Y	有形资产/负债合计
tangasset_to_intdebt	float	Y	有形资产/带息债务
tangibleasset_to_netdebt	float	Y	有形资产/净债务
ocf_to_debt	float	Y	经营活动产生的现金流量净额/负债合计
ocf_to_interestdebt	float	N	经营活动产生的现金流量净额/带息债务
ocf_to_netdebt	float	N	经营活动产生的现金流量净额/净债务
ebit_to_interest	float	N	已获利息倍数(EBIT/利息费用)
longdebt_to_workingcapital	float	N	长期债务与营运资金比率
ebitda_to_debt	float	N	息税折旧摊销前利润/负债合计
turn_days	float	Y	营业周期
roa_yearly	float	Y	年化总资产净利率
roa_dp	float	Y	总资产净利率(杜邦分析)
fixed_assets	float	Y	固定资产合计
profit_prefin_exp	float	N	扣除财务费用前营业利润
non_op_profit	float	N	非营业利润
op_to_ebt	float	N	营业利润／利润总额
nop_to_ebt	float	N	非营业利润／利润总额
ocf_to_profit	float	N	经营活动产生的现金流量净额／营业利润
cash_to_liqdebt	float	N	货币资金／流动负债
cash_to_liqdebt_withinterest	float	N	货币资金／带息流动负债
op_to_liqdebt	float	N	营业利润／流动负债
op_to_debt	float	N	营业利润／负债合计
roic_yearly	float	N	年化投入资本回报率
total_fa_trun	float	N	固定资产合计周转率
profit_to_op	float	Y	利润总额／营业收入
q_opincome	float	N	经营活动单季度净收益
q_investincome	float	N	价值变动单季度净收益
q_dtprofit	float	N	扣除非经常损益后的单季度净利润
q_eps	float	N	每股收益(单季度)
q_netprofit_margin	float	N	销售净利率(单季度)
q_gsprofit_margin	float	N	销售毛利率(单季度)
q_exp_to_sales	float	N	销售期间费用率(单季度)
q_profit_to_gr	float	N	净利润／营业总收入(单季度)
q_saleexp_to_gr	float	Y	销售费用／营业总收入 (单季度)
q_adminexp_to_gr	float	N	管理费用／营业总收入 (单季度)
q_finaexp_to_gr	float	N	财务费用／营业总收入 (单季度)
q_impair_to_gr_ttm	float	N	资产减值损失／营业总收入(单季度)
q_gc_to_gr	float	Y	营业总成本／营业总收入 (单季度)
q_op_to_gr	float	N	营业利润／营业总收入(单季度)
q_roe	float	Y	净资产收益率(单季度)
q_dt_roe	float	Y	净资产单季度收益率(扣除非经常损益)
q_npta	float	Y	总资产净利润(单季度)
q_opincome_to_ebt	float	N	经营活动净收益／利润总额(单季度)
q_investincome_to_ebt	float	N	价值变动净收益／利润总额(单季度)
q_dtprofit_to_profit	float	N	扣除非经常损益后的净利润／净利润(单季度)
q_salescash_to_or	float	N	销售商品提供劳务收到的现金／营业收入(单季度)
q_ocf_to_sales	float	Y	经营活动产生的现金流量净额／营业收入(单季度)
q_ocf_to_or	float	N	经营活动产生的现金流量净额／经营活动净收益(单季度)
basic_eps_yoy	float	Y	基本每股收益同比增长率(%)
dt_eps_yoy	float	Y	稀释每股收益同比增长率(%)
cfps_yoy	float	Y	每股经营活动产生的现金流量净额同比增长率(%)
op_yoy	float	Y	营业利润同比增长率(%)
ebt_yoy	float	Y	利润总额同比增长率(%)
netprofit_yoy	float	Y	归属母公司股东的净利润同比增长率(%)
dt_netprofit_yoy	float	Y	归属母公司股东的净利润-扣除非经常损益同比增长率(%)
ocf_yoy	float	Y	经营活动产生的现金流量净额同比增长率(%)
roe_yoy	float	Y	净资产收益率(摊薄)同比增长率(%)
bps_yoy	float	Y	每股净资产相对年初增长率(%)
assets_yoy	float	Y	资产总计相对年初增长率(%)
eqt_yoy	float	Y	归属母公司的股东权益相对年初增长率(%)
tr_yoy	float	Y	营业总收入同比增长率(%)
or_yoy	float	Y	营业收入同比增长率(%)
q_gr_yoy	float	N	营业总收入同比增长率(%)(单季度)
q_gr_qoq	float	N	营业总收入环比增长率(%)(单季度)
q_sales_yoy	float	Y	营业收入同比增长率(%)(单季度)
q_sales_qoq	float	N	营业收入环比增长率(%)(单季度)
q_op_yoy	float	N	营业利润同比增长率(%)(单季度)
q_op_qoq	float	Y	营业利润环比增长率(%)(单季度)
q_profit_yoy	float	N	净利润同比增长率(%)(单季度)
q_profit_qoq	float	N	净利润环比增长率(%)(单季度)
q_netprofit_yoy	float	N	归属母公司股东的净利润同比增长率(%)(单季度)
q_netprofit_qoq	float	N	归属母公司股东的净利润环比增长率(%)(单季度)
equity_yoy	float	Y	净资产同比增长率
rd_exp	float	N	研发费用
update_flag	str	N	更新标识
"""
import pandas as pd
import tushare as ts
#import mysql.connector
from datetime import datetime,timedelta
from apt.qsp_universal.base import base as data
from apt.vendor.tspro.data import data as tspro_data
from apt.vendor.tspro.finance import finance as finance
from sqlalchemy import create_engine,exc,delete,text 

class finance_indicator(finance):
    def __init__(self):
        super().__init__()
        #继承来自tspro_data的属性和方法 
        self.table_name = 'tspro_finance_indicator'
        self.fields = [
            'ts_code', 'ann_date', 'end_date', 'eps', 'dt_eps', 'total_revenue_ps', 'revenue_ps', 'capital_rese_ps', 'surplus_rese_ps', 'undist_profit_ps', 'extra_item', 'profit_dedt', 'gross_margin', 'current_ratio', 'quick_ratio', 'cash_ratio', 'invturn_days', 'arturn_days', 'inv_turn', 'ar_turn', 'ca_turn', 'fa_turn', 
            'assets_turn', 'op_income', 'valuechange_income', 'interst_income', 'daa', 'ebit', 'ebitda', 'fcff', 'fcfe', 'current_exint', 'noncurrent_exint', 'interestdebt', 'netdebt', 'tangible_asset', 'working_capital', 'networking_capital', 'invest_capital', 'retained_earnings', 'diluted2_eps', 'bps', 'ocfps', 'retainedps', 
            'cfps', 'ebit_ps', 'fcff_ps', 'fcfe_ps', 'netprofit_margin', 'grossprofit_margin', 'cogs_of_sales', 'expense_of_sales', 'profit_to_gr', 'saleexp_to_gr', 'adminexp_of_gr', 'finaexp_of_gr', 'impai_ttm', 'gc_of_gr', 'op_of_gr', 'ebit_of_gr', 'roe', 'roe_waa', 'roe_dt', 'roa', 'npta', 'roic', 'roe_yearly', 'roa2_yearly', 
            'roe_avg', 'opincome_of_ebt', 'investincome_of_ebt', 'n_op_profit_of_ebt', 'tax_to_ebt', 'dtprofit_to_profit', 'salescash_to_or', 'ocf_to_or', 'ocf_to_opincome', 'capitalized_to_da', 'debt_to_assets', 'assets_to_eqt', 'dp_assets_to_eqt', 'ca_to_assets', 'nca_to_assets', 'tbassets_to_totalassets', 'int_to_talcap', 
            'eqt_to_talcapital', 'currentdebt_to_debt', 'longdeb_to_debt','ocf_to_shortdebt', 'debt_to_eqt', 'eqt_to_debt', 'eqt_to_interestdebt', 'tangibleasset_to_debt', 'tangasset_to_intdebt', 'tangibleasset_to_netdebt', 'ocf_to_debt', 'ocf_to_interestdebt', 'ocf_to_netdebt', 'ebit_to_interest', 'longdebt_to_workingcapital', 
            'ebitda_to_debt', 'turn_days', 'roa_yearly', 'roa_dp', 'fixed_assets', 'profit_prefin_exp', 'non_op_profit', 'op_to_ebt', 'nop_to_ebt', 'ocf_to_profit', 'cash_to_liqdebt', 'cash_to_liqdebt_withinterest', 'op_to_liqdebt', 'op_to_debt', 'roic_yearly', 'total_fa_trun', 'profit_to_op', 'q_opincome', 'q_investincome', 
            'q_dtprofit', 'q_eps', 'q_netprofit_margin', 'q_gsprofit_margin', 'q_exp_to_sales', 'q_profit_to_gr', 'q_saleexp_to_gr', 'q_adminexp_to_gr', 'q_finaexp_to_gr', 'q_impair_to_gr_ttm', 'q_gc_to_gr', 'q_op_to_gr', 'q_roe', 'q_dt_roe', 'q_npta', 'q_opincome_to_ebt', 'q_investincome_to_ebt', 'q_dtprofit_to_profit', 'q_salescash_to_or', 'q_ocf_to_sales', 'q_ocf_to_or', 
            'basic_eps_yoy', 'dt_eps_yoy', 'cfps_yoy', 'op_yoy', 'ebt_yoy', 'netprofit_yoy', 'dt_netprofit_yoy', 'ocf_yoy', 'roe_yoy', 'bps_yoy', 'assets_yoy', 'eqt_yoy', 'tr_yoy', 'or_yoy', 'q_gr_yoy', 'q_gr_qoq', 'q_sales_yoy', 'q_sales_qoq', 'q_op_yoy', 'q_op_qoq', 'q_profit_yoy', 'q_profit_qoq', 'q_netprofit_yoy', 'q_netprofit_qoq', 'equity_yoy', 'rd_exp', 'update_flag'
        ]

    def create_table(self):
        """
        创建mysql数据表
        表名：tspro_finance_indicator
        说明：财务指标表
        """
        df_dict = self.get_data_dict()
        table_name = self.table_name    #这里调用初始化时的全局变量
        fields_dict = df_dict.set_index('字段').to_dict()['类型']
        fields = [f"{key} {value}" for key, value in fields_dict.items()]     
        query = text(f"CREATE TABLE {self.table_name} ({', '.join(fields)})")
        with self.engine.connect() as conn:
            conn.execute(query)
    def delete_duplicate(self , db = pd.DataFrame()):
        """
        目的：删除重复数据
        输入：在查询时检索到的数据+数据库中的数据
        输出：去重后的数据（按照'code','end_date','update_flag'这三列为基准）
        """
        # 找出重复的行
        duplicates = db.duplicated(subset=['code','end_date','update_flag'], keep='first')        
        # 打印出重复的行
        print(db[duplicates])
        #在数据库中删除这些行，按照id删除
        for index, row in db[duplicates].iterrows():
            with self.engine.connect() as conn:
                sql = text(f"delete from {self.table_name} where id = :id")
                conn.execute(sql, id=row['id'])
                print(f"删除重复数据：{row['id']} {row['code']} {row['end_date']} {row['update_flag']}")
    def update_finance_indicator(self , flag_delete_duplicate = False):
        """
        更新财务指标数据
        输入：继承自tspro_data的属性
        code：证券代码
        end_date：报告期日期
        flag_delete_duplicate：是否删除重复数据，默认为False
        """
        #日期校验，如果end_date有数据，必须在下面几个日期中：0331,0630,0930,1231
        if self.end_date.date().strftime('%m%d') not in ['0331','0630','0930','1231']:
            raise ValueError('end_date日期非法，请检查')
        #print(self.fields)
        #####从API接口取出财务数据#####
        df_api = self.pro.fina_indicator(**{
                "ts_code": self.code,
                "ann_date": "",
                "start_date": "",
                "end_date": self.end_date.date().strftime('%Y%m%d'),
                "period": "",
                "update_flag": "",
                "limit": "",
                "offset": ""
            }, fields=self.fields)
        #####数据适配#####
        if df_api.empty:
            df_api = pd.DataFrame(columns=self.fields)
            df_api.rename(columns={'ts_code':'code'}, inplace=True)
        else:
            #有数据，进行适配
            #更改列名
            df_api.rename(columns={'ts_code':'code'}, inplace=True)
            #更改数据类型
            df_api['ann_date'] = pd.to_datetime(df_api['ann_date'])
            df_api['end_date'] = pd.to_datetime(df_api['end_date'])
            #'update_flag'为tinyint
            df_api['update_flag'] = df_api['update_flag'].astype('int')
            #print(df_api)
            e_date = df_api['end_date'].iloc[0].date()
            s_date = df_api['end_date'].iloc[-1].date()
            #ann_date进行修正，缺失的值进行填充（Fix Future Warnin）
            #两种修正方式：
            #1. 中间值缺失，对ann_date进行向前填充
            #2. 首位值缺失，用end_date进行填充       
            df_api['ann_date'] = df_api['ann_date'].ffill()
            if pd.isnull(df_api.loc[0, 'ann_date']):
                df_api.loc[0, 'ann_date'] = df_api.loc[0, 'end_date']    
            #####从数据库中取出财务数据#####
            sql_db = f"select * from {self.table_name} where code = '{self.code}' and end_date between '{s_date}' and '{e_date}'"
            df_db = pd.read_sql(sql=sql_db, con=self.engine)
            #判断是否进行数据校验
            if flag_delete_duplicate:
                #删除重复数据
                self.delete_duplicate(df_db)
            #删除id列
            df_db.drop(columns='id', inplace=True)
            #print(df_db)
            if df_db.empty:
                pass
                #df_db = pd.DataFrame(columns=self.fields)
            else:
                df_db['ann_date'] = pd.to_datetime(df_db['ann_date'])
                df_db['end_date'] = pd.to_datetime(df_db['end_date'])  
                df_db['update_flag'] = df_db['update_flag'].astype('int')                              
            #数据取差集                        
            #df_api = df_api.append(df_db).drop_duplicates(subset=['code','end_date','update_flag'], keep=False)
            #Feature Warning Fix
            df_api = df_api.dropna(how='all', axis=1)
            df_db = df_db.dropna(how='all', axis=1)
            df_api = pd.concat([df_api, df_db ]).drop_duplicates(subset=['code','end_date','update_flag'], keep=False)
            #print(df_api)
        #####数据入库#####
        if not df_api.empty:
            #print(df_api)
            df_api.to_sql(
                name=self.table_name, 
                con=self.engine, 
                if_exists='append', 
                index=False)
            print(f"{self.code}财务指标数据已更新，数量：{len(df_api)}条")
        else:
            print(f"{self.code}财务指标数据在区间内无更新内容")
        return df_api
        
    def get_data_dict(self):
        """
        从excel文件中取出数据词典
        """              
        try:
            df = pd.read_excel(io = '.\\data\\tspro_finance\\finance_dict.xlsx', sheet_name='finance_indicator', header=0 , engine = 'openpyxl')
        except Exception as e:
            #print(str(e))
            return pd.DataFrame()
        return df
    
    def query(self, **kwargs):
        """
        查询财务指标数据
        接受多参数查询，格式如下是输入where后的条件串
        a.query(str = "code = '873132.BJ' and end_date between '2021-01-01' and '2023-12-31'")
        备注：目前本模块只包括基础的字符串，没有将常用的查询字段放入参数中
        """
        #多参数拼接，**kwargs
        sql = f"select * from {self.table_name} where 1=1"
        for key, value in kwargs.items():
            sql += f" and {value}"
        #进行数据库查询
        df = pd.read_sql(sql=sql, con=self.engine)
        return df
    
if __name__ == '__main__':
    a = finance_indicator()
    a.code = '000001.sz'
    a.start_date = datetime(2020,1,1)
    a.end_date = datetime(2024,3,31)
    #功能演示1：查询某个股票在一段时间内的财务指标数据
    #a.query(str = "code = '873132.BJ' and end_date between '2021-01-01' and '2023-12-31'")
    #功能演示2：更新财务指标数据
    df = a.update_finance_indicator(flag_delete_duplicate=True)
    #功能演示3：删除重复行
    a.delete_duplicate()
    print(df)
    #a.create_table()
    df = a.get_k_data()
    print(df) 
    a.get_data_dict()
    print(a.get_data_dict()['字段'].to_list())
    a.update_finance_indicate()
    a.roe_yearly()
    # a.upda


    

