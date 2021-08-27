import warnings

warnings.filterwarnings('ignore')

import datetime

import numpy as np
import pandas as pd

# global vars

first_n_funds=5
aggressive_rate=6

def log(text): print(str(datetime.datetime.now()).split('.')[0],text)

# read data
log('reading data...')
funds_code_df=pd.read_csv('data/funds_table.csv',usecols=['Symbol','Name'])
funds_code_df.columns=[x.lower() for x in funds_code_df.columns]
funds_history=pd.read_csv('data/funds_data.csv')
funds_history['Date']=pd.to_datetime(funds_history['Date'])

revenue_days=[1,5,10,22,66,120,250]
revenue_cols=['day','week','biweek','month','3_month','6_month','year']
revenue_zip=zip(revenue_days,revenue_cols)

col1=[]
col2=[]

funds_history['%_change']=(funds_history['Adj Close']-funds_history['Adj Close'].shift(1))/funds_history['Adj Close'].shift(1)*100

## add holidays
funds_history=funds_history[funds_history['%_change']!=0]

log('calculating revenue and max withdraw...')
for day in revenue_days:
    funds_history['lag_%s'%day]=funds_history.groupby('symbol')['Adj Close'].shift(day)

for day,col in revenue_zip:
    funds_history['%s_revenue'%col]=(funds_history['Adj Close']-funds_history['lag_%s'%day])/funds_history['lag_%s'%day]*100
    col2.append('%s_revenue'%col)
    if not col in ['day','year']:
        funds_history['%s_max_withdraw'%col]=funds_history.groupby('symbol')['Adj Close'].transform(lambda x:(x.rolling(day).max()-x)/x.rolling(day).max()*100)
        col1.append('%s_max_withdraw'%col)

cols=['symbol','Date', 'Adj Close']+col1+col2
funds_history=funds_history[cols]
funds_withdraw=funds_history[funds_history.Date>pd.to_datetime(datetime.datetime.now().date()-datetime.timedelta(days=500))].groupby('symbol',as_index=False)[col1].max()
aa=funds_history[funds_history.Date>pd.to_datetime(datetime.datetime.now().date()-datetime.timedelta(500))]
to_del=[str(x).zfill(6) for x in set(aa[aa.month_revenue.isnull()].symbol)]
funds_history=funds_history[~funds_history.symbol.isin(to_del)]

funds_select=funds_history.sort_values('Date').groupby('symbol',as_index=False).apply(lambda x:x.iloc[-1])[[x for x in funds_history.columns if x not in col1]]
funds_select=funds_select.merge(funds_withdraw,on='symbol')
funds_select=funds_select.merge(funds_code_df,on='symbol',how='left')
funds_select.reset_index(drop=True,inplace=True)

log('calculating sharpe...')
def downward_std(df):
    ls=df.iloc[-180:].values
    return np.std([x for x in ls if x <1][-180:])

funds_history['day_revenue']=funds_history['day_revenue'].astype(float)

df_dstd=funds_history.groupby('symbol',as_index=False)['day_revenue'].apply(downward_std)
df_dstd['week_revenue']=funds_history.groupby('symbol')['week_revenue'].apply(downward_std).values
df_dstd['month_revenue']=funds_history.groupby('symbol')['month_revenue'].apply(downward_std).values
df_dstd['3_month_revenue']=funds_history.groupby('symbol')['3_month_revenue'].apply(downward_std).values
df_dstd.columns=[x.replace('revenue','downward_std') for x in df_dstd.columns]
funds_select=funds_select.merge(df_dstd,on='symbol')

col3=['week_sharpe','month_sharpe','3_month_sharpe']
funds_select['week_sharpe']=funds_select['week_revenue']/funds_select['week_downward_std']
funds_select['month_sharpe']=funds_select['month_revenue']/funds_select['month_downward_std']
funds_select['3_month_sharpe']=funds_select['3_month_revenue']/funds_select['3_month_downward_std']


log('filtering data...')
funds_select=funds_select[funds_select['week_sharpe']!=np.inf]
funds_select=funds_select[funds_select['month_sharpe']!=np.inf]
funds_select=funds_select[funds_select['3_month_sharpe']!=np.inf]

funds_select=funds_select[funds_select.month_revenue.astype(float)>0]
funds_select=funds_select[funds_select['3_month_revenue'].astype(float)>0]
funds_select=funds_select[funds_select.year_revenue.astype(float)>0]

funds_select=funds_select[funds_select.year_revenue>np.quantile(funds_select.year_revenue,0.8)]


log('normalization...')
for col in col1+col2:
    funds_select[col]=funds_select[col].transform(lambda x:round(x,2))
funds_select.drop_duplicates(inplace=True)

for col in col1:
    funds_select['%s_norm_1'%col]=1/funds_select[col]
    funds_select=funds_select[funds_select['%s_norm_1'%col]!=np.inf]
    funds_select['%s_norm_1'%col]=funds_select['%s_norm_1'%col]-funds_select['%s_norm_1'%col].min()
    funds_select['%s_norm_1'%col]=funds_select['%s_norm_1'%col]/funds_select['%s_norm_1'%col].max()

for col in col2:
    funds_select['%s_norm_2'%col]=funds_select[col]-funds_select[col].min()
    funds_select['%s_norm_2'%col]=funds_select['%s_norm_2'%col]/funds_select['%s_norm_2'%col].max()

for col in col3:
    funds_select['%s_norm_3'%col]=funds_select[col]-funds_select[col].min()
    funds_select['%s_norm_3'%col]=funds_select['%s_norm_3'%col]/funds_select['%s_norm_3'%col].max()

eval_col1=[x for x in funds_select.columns if 'norm_1' in x]
eval_col2=[x for x in funds_select.columns if 'norm_2' in x]
eval_col3=[x for x in funds_select.columns if 'norm_3' in x]


log('socring...')
result=funds_select.copy()
result['withdraw_score']=np.sum(result[eval_col1],axis=1)
result['withdraw_score']=result['withdraw_score'].transform(lambda x:x-x.min())
result['withdraw_score']=result['withdraw_score'].transform(lambda x:x/x.max())
result['withdraw_score']=result['withdraw_score'].transform(lambda x:x**0.5)
result['withdraw_score']=(result['withdraw_score']*100).transform(lambda x:round(x,2))

result['revenue_score']=np.sum(result[eval_col2],axis=1)
result['revenue_score']=result['revenue_score'].transform(lambda x:x-x.min())
result['revenue_score']=result['revenue_score'].transform(lambda x:x/x.max())
result['revenue_score']=result['revenue_score'].transform(lambda x:x**0.5)
result['revenue_score']=(result['revenue_score']*100).transform(lambda x:round(x,2))

result['sharpe_score']=np.sum(result[eval_col3],axis=1)
result['sharpe_score']=result['sharpe_score'].transform(lambda x:x-x.min())
result['sharpe_score']=result['sharpe_score'].transform(lambda x:x/x.max())
result['sharpe_score']=result['sharpe_score'].transform(lambda x:x**0.5)
result['sharpe_score']=(result['sharpe_score']*100).transform(lambda x:round(x,2))


for risk_factor in [x*10 for x in range(1,10)]:
    result['%s%%_aggressive_score'%risk_factor]=result['withdraw_score']*(1-risk_factor/100)+result['revenue_score']*risk_factor/100
    result['%s%%_aggressive_score'%risk_factor]=result['%s%%_aggressive_score'%risk_factor]-result['%s%%_aggressive_score'%risk_factor].min()
    result['%s%%_aggressive_score'%risk_factor]=result['%s%%_aggressive_score'%risk_factor]/result['%s%%_aggressive_score'%risk_factor].max()
    result['%s%%_aggressive_score'%risk_factor]=(result['%s%%_aggressive_score'%risk_factor]*100).transform(lambda x:round(x,2))

log('outputing...')
# score_cols=['%s%%_aggressive_score'%(x*10) for x in range(1,10)]
# cols=['symbol', 'name','withdraw_score','revenue_score', 
#         'week_revenue', 'month_revenue', '3_month_revenue', '6_month_revenue', 'year_revenue', 
#         'week_max_withdraw', 'month_max_withdraw', '3_month_max_withdraw']+score_cols+['sharpe_score']
# result_t=result[cols].sort_values(by=['%s0%%_aggressive_score'%aggressive_rate],ascending=False)





for aggressive_rate in [3,6,9]:
    cols=['symbol','withdraw_score','revenue_score','sharpe_score','%s0%%_aggressive_score'%aggressive_rate,
            'week_revenue', 'month_revenue', '3_month_revenue',
            '6_month_revenue', 'year_revenue', 
            'week_max_withdraw', 'month_max_withdraw', 
            '3_month_max_withdraw', '6_month_max_withdraw', 
            'week_sharpe', 'month_sharpe', '3_month_sharpe']
    result_t=result.sort_values(by=['%s0%%_aggressive_score'%aggressive_rate],ascending=False)
    result_t=result_t.head(20).sort_values('sharpe_score',ascending=False).head(first_n_funds*2)
    result_t.to_excel('res/%s_%s_result_filtered.xlsx'%(str(datetime.datetime.now().date()).replace('-',''),aggressive_rate),index=False)

    # display(result_t[['symbol','withdraw_score','revenue_score',
    #                 'sharpe_score','%s0%%_aggressive_score'%aggressive_rate]].reset_index(drop=True))
    display(result_t[cols].reset_index(drop=True))

