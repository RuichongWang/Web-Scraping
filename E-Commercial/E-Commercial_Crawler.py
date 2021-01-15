"""
when using requests.request, this will lead to a verification after 10-15 visitings
this verification include slider verification, verification code to your email, etc.
changing headers, referers in pyppeteer or selenium is not working

But this website will not block the frequent request from same session 
my solution is to use session which successfully avoid it
but if the session stops and a new session started
the very same cookies will lead to a tricky verification
so change cookies everytime you run the get_sell_info func
"""

cookie='YOUR_OWN_COOKIES'

import os
import random
import re
import socket
import json

import pandas as pd
import requests
from bs4 import BeautifulSoup

raw_list=['ADDRESS_MASKED_af/category/30.html?categoryBrowse=y&origin=n&CatId=30&spm=a2g0o.category_nav.1.328.4fc648b6Ihux0q&catName=security-protection',
          'ADDRESS_MASKED_af/category/200217837.html?categoryBrowse=y&origin=n&CatId=200217837&spm=a2g0o.productlist.0.0.5c063fd48rj6uW&catName=anti-theft-lock']

# extract cat_name and cat_id
total_list=[[re.findall('category\/.*?\.',x)[0][len('category')+1:-1],re.findall('catName.*',x)[0][len('catName')+1:-len('&CatId')]] for x in raw_list]

s = requests.Session()
s.headers.update({'accept': 'application/json, text/plain, */*'})
s.headers.update({'accept-encoding': 'gzip, deflate, br'})
s.headers.update({'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8'})
s.headers.update({'cookie': cookie})
s.headers.update({'sec-fetch-mode': 'cors'})
s.headers.update({'sec-fetch-site': 'same-origin'})
s.headers.update({'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'})

def get_sell_info(cat_id,cat_name):
    res=[]
    for i in range(25):  # use multi-threads when crawling for more pages, e.g.: 5000 pages
        url="ADDRESS_MASKED/glosearch/api/product?trafficChannel=main&catName=%s&CatId=%s&ltype=wholesale&SortType=total_tranpro_desc&page=%s&groupsort=1&isrefine=y&origin=y"%(cat_name,cat_id,(str(i+1)))
        r = s.get(url,timeout=15)
        html_text=r.text    # After visited this api link, it will return a json
        
        res_temp=json.loads(html_text)
        # res_temp.keys()    
        #['abtest', 'breadCrumb', 'debugInfos', 'displayStyle', 
        # 'exposureParams', 'groupSort', 'items', 'mods', 'p4pObjectConfig', 
        # 'premium', 'refineBrand', 'refineCategory', 'refineFeatureSwitch', 
        # 'refineOrder', 'refinePrice', 'refineShipFromCountries', 'resultCount', 
        # 'resultSizePerPage', 'resultType', 'seoCrossLink', 'seoImageText', 
        # 'sortBy', 'success', 'translateResult', 'translateStatData']
        
        # we only care about items, 
        # this will return a list with the length of 60 (60 items per page)
        res_temp=res_temp['items'] 
        # res_temp.keys() 
        # ['discount', 'imageHeight', 'imageUrl', 'imageWidth', 'logisticsDesc', 
        # 'originalPrice', 'price', 'productDetailUrl', 'productId', 
        # 'productType', 'saleMode', 'saleUnit', 'sellingPoints', 'starRating', 
        # 'store', 'tags', 'title', 'traceInfo', 'tradeDesc', 'umpPrices']
        res.extend(res_temp)
    return res

res_1=[]
for cat_id,cat_name in total_list:
    res_1.extend(get_sell_info(cat_id,cat_name))

def clean_data(res_temp):
    # deal with dict/json
    temp=[]
    for key in keys:
        try:
            temp.append(res_temp[key])
        except:temp.append('na')
    return temp

keys=['productId','title','productDetailUrl','price','logisticsDesc','tradeDesc']   # info that we interested in 
res = list(map(lambda x:clean_data(x),res_1))
pd.DataFrame(res, columns=keys).to_csv('res.csv',index=False)

