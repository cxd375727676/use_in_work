# -*- coding: utf-8 -*-
"""
Created on Fri Jul 31 09:35:09 2020

@author: win 8
"""
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = ['sans-serif']
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['figure.dpi'] = 100


def get_performance(month_ret, risk_free, fmt=True):
    """ 月度收益率序列评价指标 """
    if isinstance(month_ret, pd.Series):
        month_ret = month_ret.to_frame()
    cum_ret_multiplier = (month_ret + 1).cumprod()
    # 年化收益率
    annual_ret = cum_ret_multiplier.iloc[-1].pow(12 / len(month_ret)) - 1
    # 年化波动率
    annual_vol = month_ret.std() * pow(12, 0.5)
    # 夏普比率，注意是超额收益的均值除以超额收益的标准差【这里无风险利率不是常数】
    abnormal_ret = month_ret.sub(risk_free, axis=0)
    sp = (abnormal_ret.mean() * 12) / (abnormal_ret.std() * pow(12, 0.5))  
    # 最大回撤，我的独创！！！
    max_draw_down = (cum_ret_multiplier / cum_ret_multiplier.expanding().max()).min() - 1
    
    res = pd.concat([annual_ret, annual_vol, sp, max_draw_down], axis=1)
    res.columns = ['年化复合收益率', '年化波动率', '夏普比率', '最大回撤']
    
    start = month_ret.index[0].strftime("%Y/%m")
    end = month_ret.index[-1].strftime("%Y/%m")
    res.columns.name = f"{start}-{end}"
    
    if fmt:
        for col in ['年化复合收益率', '年化波动率', '最大回撤']:
            res[col] = res[col].map(lambda x: '%.2f%%' % (x * 100))
        res['夏普比率'] = res['夏普比率'].map(lambda x: '%.3f' % x)  
    return res.T   

 
data = pd.read_excel('data_assets.xlsx', index_col=0)
def get_security_rets(securities, start, end):
    return data.loc[start: end, securities]     



class Account:
    def __init__(self, init_dt, init_weight):
        self.pre_dt = init_dt              # 上一个调仓日
        self.pre_weight = init_weight      # 当前调仓最新权重
    
    def trail(self, dt):
        """ 权重、收益率自发演化 """
        pre_securities = list(self.pre_weight.keys())
        security_rets = get_security_rets(pre_securities, self.pre_dt, dt)  
        security_rets.iloc[0] = 0   # 第一个收益率不用，为方便后续计算，设为0
            
        # 假设期间组合初始净值为1
        security_nv = (security_rets + 1).cumprod() * self.pre_weight  # 各标的净值
        poto_nv = security_nv.sum(axis=1)                   # 期间组合净值
        poto_ret = poto_nv.pct_change()                       # 组合收益率
        weight = security_nv.div(poto_nv, axis='index')     # 各标的权重
        self.prev_weight = weight.iloc[-1].to_dict()       # 储存自发演化最后的权重      
        self._weight = weight
        self._ret = poto_ret
        
    def rebalance(self, dt, new_weight):
        self.pre_dt = dt
        self.pre_weight = new_weight
        
            
        
class BackTest:
    def __init__(self, adjust_dates, end_date, init_weight):
        self.start_date = adjust_dates[0]  # 调仓日列表第一个是建仓日期
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        self.adjust_dates = adjust_dates
        self.account = Account(self.start_date, init_weight)
    
    def get_new_weight(self, *args, **kwargs):
        """ 可修改模块 """
        return {'股票': 0.25, '国债': 0.25, '黄金': 0.25, '大宗商品': 0.25}

    def run(self):
        weight = []
        ret = []
        for i, adjust_date in enumerate(self.adjust_dates[1:]):
            self.account.trail(adjust_date)
            new_weight = self.get_new_weight()
            self.account.rebalance(adjust_date, new_weight)
            
            if i == 0:
                ret.append(self.account._ret)
            else:
                ret.append(self.account._ret.iloc[1:])
            weight.append(self.account._weight.iloc[:-1])
            
            
        self.account.trail(datetime.strptime(end_date, '%Y-%m-%d'))
        ret.append(self.account._ret.iloc[1:])
        weight.append(self.account._weight)
        
        ret = pd.concat(ret, sort=True)
        self.ret = ret
        nv = (ret + 1).cumprod()
        nv.iloc[0] = 1   # 初始净值为1
        self.net_value = nv
        self._weight = pd.concat(weight, sort=True).astype(pd.SparseDtype())

    @property
    def weight(self):
        return self._weight.sparse.to_dense()
    
    def plot(self):
        self.net_value.plot(title='组合净值图')
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
            
            
            
 # 测试
adjust_dates = data.loc['2010-01-01': '2020-4-30'].index.tolist()
end_date = '2020-05-29'
init_weight = {'股票': 0.25, '国债': 0.25, '黄金': 0.25, '大宗商品': 0.25}
bt = BackTest(adjust_dates, end_date, init_weight)
bt.run()

bt.weight.head()
bt.weight.tail()

bt.ret
bt.net_value
           