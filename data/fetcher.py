import os
import gzip
import zipfile

import pandas as pd
from data.enums import COLUMN_CONFIG
from data.utils import get_path_subset, get_ticker_path

class TickData:
    def __init__(self):
        self._data = {}
        
    def __getitem__(self, key):
        return self._data[key]
    
    def keys(self):
        return self._data.keys()
    def values(self):
        return self._data.values()
    def items(self):
        return self._data.items()
    
    def fetch(self, start_dt, end_dt, ticker) -> dict:
        """
        Must return dictionary with exchange name key and tick data Dataframe value. 
        """
        if "binance_spot" not in self._data.keys():
            self.fetch_binance(start_dt, end_dt, 'spot', ticker) 
        if "binance_future" not in self._data.keys():
            self.fetch_binance(start_dt, end_dt, 'future', ticker) 
        # if "bybit_spot" not in self._data.keys():
        #     self.fetch_bybit(start_dt, end_dt, 'spot', ticker)
        # if "bybit_future" not in self._data.keys():
        #     self.fetch_bybit(start_dt, end_dt, 'future', ticker)
        if "okx_spot" not in self._data.keys():
            self.fetch_okx(start_dt, end_dt, 'spot', ticker)
        if "okx_future" not in self._data.keys():
            self.fetch_okx(start_dt, end_dt, 'future', ticker)
    
    def fetch_exchange(self, start_dt, end_dt, market, exchange, ticker) -> pd.DataFrame:
        if exchange == 'binance':
            return self.fetch_binance(start_dt, end_dt, market, ticker)
        if exchange == 'bybit':
            return self.fetch_bybit(start_dt, end_dt, market, ticker)
        if exchange == 'okx':
            return self.fetch_okx(start_dt, end_dt, market, ticker)
        
    def fetch_binance(self, start_dt, end_dt, market='spot', ticker='BTCUSDT'):   
        if f'binance_{market}_{ticker}' in self._data.keys():
            return self._data[f"binance_{market}_{ticker}"]
            
        base_dir = get_ticker_path('binance', market, ticker)
        
        file_list = os.listdir(base_dir)
        subfile_list = get_path_subset(file_list, start_dt, end_dt)
        
        df_list = []
        for i, path in enumerate(subfile_list, start=1):
            print(f"[{i}/{len(subfile_list)}] Fetching Data from {path}...")
            filepath = os.path.join(base_dir, path)
        
            with zipfile.ZipFile(filepath) as zf:
                filename = zf.namelist()[0]
                with zf.open(filename) as csv_file:
                    df = pd.read_csv(csv_file, header=None, low_memory=False)
                    if df.shape[1] == 7: # Spot case
                        df = df.iloc[:, :-1]
                    if df.iloc[0, 0] =='id': # Future case
                        df = df.iloc[1:, :]
                    if (df.iloc[0, :].values == ["trade_Id", "price", "qty", "quote_qty", "time", "is_buyer_maker"]).all():
                        df = df.iloc[1:, :]
                        
                    if (int(filename.split('.')[0][-10:-6]) > 2024) & (market == 'spot'):
                        # There is adjustment from 2025 at timestamp.
                        # millisec -> nanosec utc timestamp
                        df[4] = (df[4] / 1000).astype(int)
                        
            df.columns = COLUMN_CONFIG["trades"]
            df_list.append(df)
        
        final_df = pd.concat(df_list)
        final_df['time'] = final_df['time'].astype(int)
        final_df['utc_time'] = pd.to_datetime(final_df['time'], unit='ms')
        final_df['price'] = final_df['price'].astype('float')
        final_df['qty'] = final_df['qty'].astype('float')
        self._data[f'binance_{market}_{ticker}'] = final_df[['utc_time', 'time', 'price', 'qty', 'is_buyer_maker']]
        return self._data[f'binance_{market}_{ticker}']
    
    def fetch_bybit(self, start_dt, end_dt, market="spot", ticker='BTCUSDT'):
        if f'bybit_{market}_{ticker}' in self._data.keys():
            return self._data["bybit_{market}_{ticker}"]
        base_dir = get_ticker_path('bybit', market, ticker)
        file_list = os.listdir(base_dir)
        subfile_list = get_path_subset(file_list, start_dt, end_dt)

        df_list = []
        for i, path in enumerate(subfile_list, start=1):
            print(f"[{i}/{len(subfile_list)}] Fetching Data from {path}...")
            filepath = os.path.join(base_dir, path)
            
            with gzip.open(filepath, "rt") as f:
                df = pd.read_csv(f)
                df_list.append(df)
        
        final_df = pd.concat(df_list)
        final_df = final_df.rename(columns={"timestamp": 'time', "size": 'qty', 'volume': 'qty'})
        final_df['is_buyer_maker'] = (final_df['side'] == "Buy")
        final_df['time'] = (final_df['time']).astype(int)
        final_df['utc_time'] = pd.to_datetime(final_df['time'], unit='ms')
        final_df['price'] = final_df['price'].astype('float')
        final_df['qty'] = final_df['qty'].astype('float')
        self._data[f'bybit_{market}_{ticker}'] = final_df[['utc_time', 'time', 'price', 'qty', 'is_buyer_maker']]
        return self._data[f'bybit_{market}_{ticker}']
        
    def fetch_okx(self, start_dt, end_dt, market='spot', ticker='BTCUSDT'):
        if f'okx_{market}_{ticker}' in self._data.keys():
            return self._data[f"okx_{market}_{ticker}"]
        base_dir = get_ticker_path('okx', market, ticker)
        file_list = os.listdir(base_dir)
        subfile_list = get_path_subset(file_list, start_dt, end_dt)
        
        df_list = []
        for i, path in enumerate(subfile_list, start=1):
            print(f"[{i}/{len(subfile_list)}] Fetching Data from {path}...")
            filepath = os.path.join(base_dir, path)
        
            with zipfile.ZipFile(filepath) as zf:
                filename = zf.namelist()[0]
                with zf.open(filename) as csv_file:
                    df = pd.read_csv(csv_file, encoding="latin-1")
                    df.columns = ['trade_id', 'is_buyer_maker', 'qty', 'price', 'time']
                    df = df.sort_values("time")
                    df_list.append(df)
        
        final_df = pd.concat(df_list)
        final_df = final_df.rename(columns={"timestamp": 'time', "size": 'qty'})
        final_df['is_buyer_maker'] = (final_df['is_buyer_maker'] == "buy")
        final_df['utc_time'] = pd.to_datetime(final_df['time'], unit='ms')
        final_df['price'] = final_df['price'].astype('float')
        final_df['qty'] = final_df['qty'].astype('float')
        self._data[f'okx_{market}_{ticker}'] = final_df[['utc_time', 'time', 'price', 'qty', 'is_buyer_maker']]
        return self._data[f'okx_{market}_{ticker}']