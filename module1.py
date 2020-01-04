from tick import tick
import tushare as ts
ts.set_token('55297f16c0119146589e059db315ba28a9412e89ec9f91e538e655b2')
#df=ts.get_hist_data('600848',start='2019-10-01',end='2019-10-15')
#print(df.columns)
#print(df[['close','volume','turnover']])
#tk=tick('512880','2019-09-26')

pro = ts.pro_api()
#通用行情接口
#df = pro.fund_daily(ts_code='510300.SZ', start_date='20180701', end_date='20180718')
#print(df)

#每日指标 积分300
#df = pro.daily_basic(ts_code='', trade_date='20180726', fields='ts_code,trade_date,turnover_rate,volume_ratio,pe,pb')
#print(df)

#每日指标 老接口
df_today=ts.get_today_all()
df_today.to_csv('.\\data\\today_all.csv', encoding='GBK')

