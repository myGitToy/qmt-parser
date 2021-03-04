from jqdatasdk import *
import pandas as pd
import datetime
import sqlalchemy
from apt.vendor.jqdata.jqdata import data as jqdata
from apt.vendor.jqdata.ETF import ETF as ETF

#显示所有列
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
auth('13817092632','JQ@tushare123')

start = datetime.datetime(2020,10,12)
end = datetime.datetime(2020,12,22)
#获取市值数据
q=query(finance.STK_BALANCE_SHEET.company_name,
        finance.STK_BALANCE_SHEET.company_id,
        finance.STK_BALANCE_SHEET.code,
        finance.STK_BALANCE_SHEET.pub_date,
        finance.STK_BALANCE_SHEET.start_date,
        finance.STK_BALANCE_SHEET.end_date,
        finance.STK_BALANCE_SHEET.report_date,
        finance.STK_BALANCE_SHEET.report_type,
        finance.STK_BALANCE_SHEET.source_id,
        finance.STK_BALANCE_SHEET.source,
        finance.STK_BALANCE_SHEET.cash_equivalents,
        finance.STK_BALANCE_SHEET.trading_assets,
        finance.STK_BALANCE_SHEET.bill_receivable,
        finance.STK_BALANCE_SHEET.account_receivable,
        finance.STK_BALANCE_SHEET.advance_payment,
        finance.STK_BALANCE_SHEET.other_receivable,
        finance.STK_BALANCE_SHEET.affiliated_company_receivable,
        finance.STK_BALANCE_SHEET.interest_receivable ,     
        finance.STK_BALANCE_SHEET.dividend_receivable,
        finance.STK_BALANCE_SHEET.inventories,
        finance.STK_BALANCE_SHEET.expendable_biological_asset,
        finance.STK_BALANCE_SHEET.non_current_asset_in_one_year,
        finance.STK_BALANCE_SHEET.total_current_assets,
        finance.STK_BALANCE_SHEET.hold_for_sale_assets,
        finance.STK_BALANCE_SHEET.hold_to_maturity_investments,
        finance.STK_BALANCE_SHEET.longterm_receivable_account,
        finance.STK_BALANCE_SHEET.longterm_equity_invest,
        finance.STK_BALANCE_SHEET.investment_property,
        finance.STK_BALANCE_SHEET.fixed_assets,
        finance.STK_BALANCE_SHEET.constru_in_process,
        finance.STK_BALANCE_SHEET.construction_materials,
        finance.STK_BALANCE_SHEET.fixed_assets_liquidation,
        finance.STK_BALANCE_SHEET.biological_assets,
        finance.STK_BALANCE_SHEET.oil_gas_assets,
        finance.STK_BALANCE_SHEET.intangible_assets,
        finance.STK_BALANCE_SHEET.development_expenditure,
        finance.STK_BALANCE_SHEET.good_will,
        finance.STK_BALANCE_SHEET.long_deferred_expense,
        finance.STK_BALANCE_SHEET.deferred_tax_assets,
        finance.STK_BALANCE_SHEET.total_non_current_assets,
        finance.STK_BALANCE_SHEET.total_assets,
        finance.STK_BALANCE_SHEET.shortterm_loan,
        finance.STK_BALANCE_SHEET.trading_liability,
 
).filter(finance.STK_BALANCE_SHEET.code=='600519.XSHG',finance.STK_BALANCE_SHEET.pub_date>='2019-01-01',finance.STK_BALANCE_SHEET.report_type==0).limit(20)
df=finance.run_query(q)
print(df)



