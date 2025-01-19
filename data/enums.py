import os 

BASE_PATH = r"C:\Users\wklee\Desktop\WKLee\FBA\Capstone\fba-capstone\data"

PATH_CONFIG = {
    # "binance_spot_sec_path": os.path.join(BASE_PATH, "binance_data_collection/data", "spot", "", "daily", "klines", "BTCUSDT", "1s"),
    "binance_spot_trades": os.path.join(BASE_PATH, "binance_data_collection/data", "spot", "", "daily", "trades"),
    "binance_future_trades": os.path.join(BASE_PATH, "binance_data_collection/data", "futures", "um", "daily", "trades"),
    
    "bybit_spot_trades": os.path.join(BASE_PATH, "bybit_data_collection", "trading", 'spot'),
    "bybit_future_trades": os.path.join(BASE_PATH, "bybit_data_collection", "trading", 'future'),
    
    "okx_spot_trades": os.path.join(BASE_PATH, "okx_data_collection", "trades", "daily", 'spot'),
    "okx_future_trades": os.path.join(BASE_PATH, "okx_data_collection", "trades", "daily", 'future')
}

COLUMN_CONFIG = {
    "trades": ["trade_Id", "price", "qty", "quote_qty", "time", "is_buyer_maker"],
    "klines": [
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
        ],
}

