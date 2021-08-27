from bs4 import BeautifulSoup
from urllib.request import urlretrieve
import os 
import pandas as pd 
import requests
import json
from selenium import webdriver
import time 
import datetime

if not os.path.exists('temp'): os.makedirs('temp')
if not os.path.exists('res'): os.makedirs('res')
if not os.path.exists('data'): os.makedirs('data')
if not os.path.exists('data/by_funds'): os.makedirs('data/by_funds')

if not os.path.exists('data/funds_table.csv'):
    driver = webdriver.Chrome('/Users/user/Downloads/网页下载/chromedriver')

    res_raw=[]
    for page in range(1,18):
        url='https://finance.yahoo.com/screener/predefined/top_mutual_funds?count=100&offset=%s00'%page
        driver.get(url)
        time.sleep(3)
        txt=driver.page_source
        txt=BeautifulSoup(txt)
        res_raw.extend(txt.find_all('tr',{'class':'simpTblRow'}))

    driver.quit()

    def parsing(bs):
        return [x.text for x in bs.find_all('td')]

    res=list(map(lambda x:parsing(x),res_raw))

    cols=['Symbol','Name','Change','% Change','Price (Intraday)','50 Day Average','200 Day Average','3-Mo Return','YTD Return','drop']
    cols=[x.replace(' ','_') for x in cols]
    funds_table=pd.DataFrame(res,columns=cols)
    funds_table.drop(columns=['drop']).to_csv('data/funds_table.csv',index=False)

funds_table=pd.read_csv('data/funds_table.csv')

funds_table['3-Mo_Return']=funds_table['3-Mo_Return'].str.replace('%','').astype(float)
funds_table['YTD_Return']=funds_table['YTD_Return'].str.replace('%','').astype(float)

symbols=funds_table.Symbol.tolist()
for symbol in symbols:
    try:urlretrieve(f'https://query1.finance.yahoo.com/v7/finance/download/{symbol}?period1=1565654400&period2=1628812800&interval=1d&events=history&includeAdjustedClose=true',f'data/by_funds/{symbol}.csv')
    except:print(symbol)

funds_files=os.listdir('data/by_funds')

res_df=pd.DataFrame()
for i,file in enumerate(funds_files):
    df=pd.read_csv('data/by_funds/%s'%file,usecols=['Date','Adj Close'])
    df['symbol']=file.split('.')[0]
    res_df=pd.concat((res_df,df))
    if not i%50:print(i+1)

res_df.to_csv('data/funds_data.csv',index=False)

