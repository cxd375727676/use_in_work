# -*- coding: utf-8 -*-
"""
Created on Mon Jul 27 09:55:10 2020

@author: win 8
"""

import pandas as pd
import re
import requests
from functools import lru_cache
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.width', 80) # 设置打印宽度(**重要**)

# 全国大学数据
# http://www.moe.gov.cn/mdcx/qggdxxmd/201912/t20191217_10000023.html
df = pd.read_excel('W020200709292792106069.xls', sheet_name='Sheet2')


@lru_cache(maxsize=32)
def get_university(province):
    idx = df['序号']
    pattern = re.compile('(?P<province>.+)（')
    province_remark = [(i, pattern.match(v).group('province')) \
                       for i, v in idx.items() if not isinstance(v, int)]
    for i, (idx, prov) in enumerate(province_remark):
        if prov == province:
            start = idx + 1
            end = province_remark[i + 1][0]
            prov_df = df.iloc[start:end, :]
            prov_df.prov = prov
            return prov_df

# bjxx = get_university('北京市')

# 一分一段数据
# https://gaokao.baidu.com/gaokao/gkschool/scoreenroll?ajax=1&query=清华大学&province=福建&curriculum=理科&batchName=本科一批
@lru_cache(maxsize=3000)
def get_score(university, origin='湖北', curriculum='文科', batchName='本科二批'):
    r = requests.get(
            'https://gaokao.baidu.com/gaokao/gkschool/scoreenroll', 
            headers = {'User-Agent': 'Mozilla/5.0'},
            params={
                    'ajax':1, 
                    'query': university, 
                    'province': origin, 
                    'curriculum': curriculum,
                    'batchName': batchName
                    })
    r.raise_for_status()
    #print(r.request.headers)
    #print(r.url)
    return r.json()

#score = get_score('长江大学文理学院')

     
def handle_score(university):  
    score = get_score(university)
    if score['msg'] == 'success' and 'minScoreOrder' in score['data']:
        data = score['data']['minScoreOrder']
        res = {}
        for item in data:
            year = item['key']
            value = item['value'][0]
            name = value['name']
            rank = value['value']
            if name == '本科二批':
                res.update({year: rank})  
        rank = {year: res.get(year, 0) for year in [2017, 2018, 2019]}
        rank = pd.DataFrame(rank, index=[university], dtype=int)   
        return rank
#cjwlxy = handel_score('长江大学文理学院')


def select_university(province, my_rank=39775):
    univ_info = get_university(province)
    univ_list = univ_info['学校名称'].tolist()
    res = []
    for univ in univ_list:
        rank = handle_score(univ)
        if rank is not None:
            res.append(rank)
    res = pd.concat(res)
    res = res.loc[(res >= my_rank).any(axis=1)].astype(int).replace(0, '--')
    return res


def plot_table(df): 
    r, c = df.shape
    plt.table(
            cellText = df.values,
            bbox=(0,0,1,1),                                   
            rowLabels=df.index,                    
            colLabels=df.columns,
            rowLoc = 'center', 
            colLoc = 'center',                                
            cellLoc='center',
            rowColours = ['#8c8c8c'] * r,    
            colColours = ['#8c8c8c'] * c,             
            fontsize=15)
    plt.gca().set_axis_off()
    plt.show()
    
    
def main():
    while True:
        s = input("\n================================\
                  \n郑佳琪分数441，排名39775名。\
                  \n查询学校近三年录取排名情况请按1\
                  \n查询指定省份可能录取学校请按2\
                  \n退出请按3\n")
        if s == '1':
            univ = input("\n请输入学校名称：")
            print("近三年排名录取排名情况如下：")
            data = handle_score(univ)
            if data is None:
                print("没有匹配的数据")
            else:
                print(data)
                #plot_table(data)
        if s == '2':
            provinces = [
                     '北京市',
                     '天津市',
                     '河北省',
                     '山西省',
                     '内蒙古自治区',
                     '辽宁省',
                     '吉林省',
                     '黑龙江省',
                     '上海市',
                     '江苏省',
                     '浙江省',
                     '安徽省',
                     '福建省',
                     '江西省',
                     '山东省',
                     '河南省',
                     '湖北省',
                     '湖南省',
                     '广东省',
                     '广西壮族自治区',
                     '海南省',
                     '重庆市',
                     '四川省',
                     '贵州省',
                     '云南省',
                     '西藏自治区',
                     '陕西省',
                     '甘肃省',
                     '青海省',
                     '宁夏回族自治区',
                     '新疆维吾尔自治区']
            print("\n所有省份列举如下：\n")
            print(" ".join(provinces))
            prov = input("\n请输入省份名称：")
            data = select_university(prov)
            if data.empty:
                print("无")
            else:
                print(data)
                #plot_table(data)
        if s == '3':
            break
        

main()
