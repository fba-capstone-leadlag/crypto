import pandas as pd
import numpy as np

import argparse
from data.fetcher import TickData

# Single Core Task
def hayashi_yoshida_estimator(df1, df2):
    # df1, df2 must have time(timestamp) and return columns 
    temp_df1 = df1.iloc[1:]['return']
    temp_df2 = df2.iloc[1:]['return']
    
    # Make interval
    I1 = pd.IntervalIndex.from_arrays(df1.index[:-1], df1.index[1:])
    I2 = pd.IntervalIndex.from_arrays(df2.index[:-1], df2.index[1:])

    # Calculate covariances
    hy_cov = 0
    minarg = 0
    for i2 in I2:
        # for each interval of df2
        
        found = False
        for i in range(minarg, len(I1)):
            # for each interval from previous interval's end
            
            if (I1[i].left < i2.right) and (I1[i].right > i2.left):
                # if overlap two intervals.
                # calculate covariance
                hy_cov += temp_df1.loc[I1[i].right] * temp_df2.loc[i2.right]
                
                # set params for next iter.
                found = True
                minarg = i

            elif I1[i].left > i2.right:
                # overlap is not init. (at the Begining)
                break
            elif I1[len(I1) - 1].right <= i2.left:
                # overlap is not init (at the End)
                break
            elif found:
                # if overlap series is ended.
                break
        
    # calculate HY estimator    
    hy_corr = hy_cov / np.sqrt(np.sum(temp_df1 ** 2) * np.sum(temp_df2 ** 2))
    return hy_corr

def fetch_df(start_dt, end_dt, market, exchange, ticker, hour, threshold=0):
    # fetch data
    tickdata = TickData()
    df = tickdata.fetch_exchange(start_dt, end_dt, market, exchange, ticker)
    tick_df = get_tick_data(df, 'time')
    
    if hour != 'all':
        left, right = map(int, hour.split(":"))
        HOUR = list(range(left, right+1))
        tick_df = tick_df[tick_df['utc_time'].dt.hour.isin(HOUR)]
        
    tick_df = tick_df[np.abs(tick_df['return']) >= threshold * (10 ** (-4))]
        
    return tick_df[['time', 'return']].set_index("time").copy()

def get_tick_data(df, grouper_time='utc_time'):
    df = df.copy()
    df['dolvol'] = df['price'] * df['qty']
    
    if grouper_time == 'utc_time':
        grouper = df['utc_time']
    elif grouper_time == 'time':
        grouper = df['time']
    else:
        raise ValueError()
    
    adjusted = df.groupby(grouper)[['dolvol', 'qty']].agg({"dolvol": 'sum', 'qty': 'sum'})
    adjusted = adjusted.reset_index()
    adjusted['price'] = adjusted['dolvol'] / adjusted['qty']
    adjusted['log_price'] = np.log(adjusted['price'])
    adjusted['return'] = adjusted['log_price'].diff()
    adjusted['prev_time'] = adjusted[grouper_time].shift(1)
    
    adjusted['utc_time'] = pd.to_datetime(adjusted['time'], unit='ms')
    return adjusted[[grouper_time, 'utc_time', 'price', 'log_price', 'return', 'prev_time']].copy()


def main():
    # Argument parsing
    parser = argparse.ArgumentParser(description="Calculate Hayashi-Yoshida Correlation")
    parser.add_argument('-L', '--Lags', type=str, required=True, help="Lag range in the format edge:step (e.g., 40:20 -> [-40, -20, 0, 20, 40])")
    parser.add_argument('-l', '--left', type=str, required=True, help="<Exchange name>:<Market>:<Ticker> (e.g., 'okx:spot:BTCUSDT')")
    parser.add_argument('-r', '--right', type=str, required=True, help="<Exchange name>:<Market>:<Ticker> (e.g., 'okx:future:BTCSUDT')")
    # parser.add_argument('-t', '--ticker', type=str, required=True, help="Coin ticker. (e.g. BTCUSDT)")
    parser.add_argument('-H', '--hour', type=str, default='all', help="<start_hour>:<end_hour>")
    parser.add_argument('-t', '--thresholds', type=int, default=0, help="<threshold> * 10^(-4)")
    
    args = parser.parse_args()

    # Extract LAGS from input
    try:
        edge, lag_step = map(int, args.Lags.split(':'))
        LAGS = list(range(-edge, edge + lag_step, lag_step))
    except ValueError:
        raise ValueError("Invalid format for --Lags. Use edge:step (e.g., 220:20)")

    START_DATE = "2024-12-25"
    END_DATE = "2025-01-05"
    EXCHANGE1, MARKET1, TICKER1 = args.left.split(":")
    EXCHANGE2, MARKET2, TICKER2 = args.right.split(":")
    HOUR = args.hour
    THRESHOLD = args.thresholds
    
    with open(f"HY-{THRESHOLD}_CORR-{HOUR.split(":")}_{EXCHANGE1}-{MARKET1}-{TICKER1}_{EXCHANGE2}-{MARKET2}-{TICKER2}_{START_DATE}-{END_DATE}.txt", 'w') as f:
        base_df1 = fetch_df(START_DATE, END_DATE, MARKET1, EXCHANGE1, TICKER1, HOUR, THRESHOLD) 
        base_df2 = fetch_df(START_DATE, END_DATE, MARKET2, EXCHANGE2, TICKER2, HOUR, THRESHOLD)
        
        for lag in LAGS:
            print(F"LAG: {lag} HY CORRELATION IS CALCULATING ...")
            df1 = base_df1.copy()
            df2 = base_df2.copy()
            
            df1.index = df1.index + lag
            hy_corr = hayashi_yoshida_estimator(df1, df2)
            f.write(f"{lag},{hy_corr}\n")
        
    
if __name__ == "__main__":
    main()