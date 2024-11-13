import pandas as pd
# import numpy as np
import matplotlib.pyplot as plt

from scipy.stats import pearsonr
from statsmodels.tsa.stattools import grangercausalitytests


def get_lag_corr(Y, X, lag=6):
    temp_df = pd.merge(Y, X, left_index=True, right_index=True, how='inner')
    
    lag_arr = list(range(-lag, lag+1))
    corr_list = []
    for lag in lag_arr:
        temp_Y = temp_df.iloc[:lag, 0] if lag < 0 else temp_df.iloc[lag:, 0]
        temp_X = temp_df.shift(lag).iloc[:lag, 1] if lag < 0 else temp_df.shift(lag).iloc[lag:, 1]
        result = pearsonr(temp_Y, temp_X)
        corr_list.append([lag, result[0], result[1]])
        
    return pd.DataFrame(corr_list, columns=["lag", "corr", "pvalue"])

def test_granger(Y, X, lag=10):
    temp_df = pd.merge(Y, X, left_index=True, right_index=True, how='inner')
    grangercausalitytests(temp_df[['btc_price', 'onchain_data']], maxlag=lag)


def plot_subplots(df, *args):
    """Plotting subplots.
    
    df: dataframe for plotting.
    *args: column name of df
    """
    if len(args) == 0:
        return 
    
    fig, ax = plt.subplots(len(args), figsize=(14, 4*len(args)))
    if len(args) == 1:
        df[args[0]].plot(ax=ax)
        ax.set_title(args[0])
        
    else:
        for i, col in enumerate(args):
            df[col].plot(ax=ax[i])
            ax[i].set_title(col)
            
    plt.tight_layout()
    plt.plot()