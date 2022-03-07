import pandas as pd
#pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)




def apply_amount(num):
    if num <= 1000000:
        return "小于百万"
    elif num >1000000 and num <=10000000:
        return "百万"
    elif num>10000000:
        return "千万"


df = pd.read_csv( ".\\data\\tick\\2020-12-21\\600030.XSHG.csv")
#df['type'] = df['type'].map({'买盘':1,'卖盘':-1,'中性盘':0})
df['amount'] = df['amount'].apply(apply_amount )
print(df.head(100))