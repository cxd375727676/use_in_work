# -*- coding: utf-8 -*-
"""
Created on Wed Aug  5 10:39:52 2020

处理Wind底层行业分类数据库

@author: win 8
"""

import pickle
import pandas as pd


def rebuild_ind_data(ind, class_std):
    """ 返回多层次索引pd.Series """
    ind = ind.copy()
    ind['ENTRY_DT'] = pd.to_datetime(ind['ENTRY_DT'])
    ind['REMOVE_DT'] = pd.to_datetime(ind['REMOVE_DT'])
    tomorrow = pd.Timestamp(pd.Timestamp.now().date() + pd.Timedelta(days=1))
    ind['REMOVE_DT'].fillna(tomorrow, inplace=True)  # 即行业最新信息，假定每日退出，方便设定区间
    
    ind['INTERVAL'] = ind.apply(lambda x: pd.Interval(
            x.at['ENTRY_DT'], x.at['REMOVE_DT'], closed='both'), axis=1)
    ind = ind[['S_INFO_WINDCODE', 'INTERVAL', class_std]].set_index(
            ['S_INFO_WINDCODE', 'INTERVAL'])[class_std]
    return ind
    

def combine_industry(data, ind, date_col, class_std):
    """ 与data合并（添加行业信息）"""
    data = data.copy()
    data[date_col] = pd.to_datetime(data[date_col])
    
    def combine_industry_helper(df):
        rpt_dates = df[date_col]
        stock = df['S_INFO_WINDCODE'].iloc[0]
        if stock in ind.index:
            interval_map = ind.loc[stock]
            intervals = pd.IntervalIndex(interval_map.index.tolist())
            value = pd.cut(rpt_dates, intervals).map(interval_map)
            df[class_std] = value
        else:
            df[class_std] = None
        return df
    
    data = data.groupby('S_INFO_WINDCODE').apply(combine_industry_helper)
    return data


    
with open("ashare_citics_ind.pickle", "rb") as rf:
    ind = pickle.load(rf)
    
with open("ashare_holder_data.pickle", "rb") as rf:
    holder = pickle.load(rf) 
data = holder.groupby(['S_INFO_WINDCODE', 'REPORT_PERIOD'], as_index=False)[
        ['S_HOLDER_COMPCODE', 'S_HOLDER_PCT']].agg(
        {'S_HOLDER_COMPCODE': 'count', 'S_HOLDER_PCT': 'sum'})
   
class_std = 'CITICS_IND_CODE'
ind_reb = rebuild_ind_data(ind, class_std)
new_data = combine_industry(data, ind_reb, 'REPORT_PERIOD', class_std)    
