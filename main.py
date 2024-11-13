# import argparse 

from data.binance_data import *
# from data.manager import *
# from config import DB_INFO, DB_INFO_P
import pandas as pd

"""
ccxt 라이브러리를 통해 바이낸스에서 불러온 OHLCV 데이터를 
ohlcv_data 데이터베이스내 테이블로 저장하는 프로그램  
ohlcv_data 에 테이블이 없다면 만들고, 아닐 경우 존재하는 테이블에 데이터를 삽입.

Ex) python3 main.py -n binance_btc_usdt_f -t BTC/USDT -s 2024-09-29 -f
"""

if __name__ == "__main__":
    
    # parser = argparse.ArgumentParser()
    # parser.add_argument("-n", "--name", action="store", help="DB에 저장할 테이블 이름")
    # parser.add_argument("-t", "--ticker", action="store", help="ccxt로 불러올 티커. ccxt에서 제공하는 티커이름과 같아야 함.")
    # parser.add_argument("-s", "--startdate", action="store", help="데이터를 언제부터 불러올 것인지. %Y-%m-%d의 형식을 따라야 함")
    # parser.add_argument("-f", "--future", action="store_true", help="선물 데이터를 불러올 것인지")
    # parser.add_argument("-p", "--private", action="store_true", default=False, help="내부 아이피를 사용중인지")
    # args = parser.parse_args()
    
    # manager = DBManager(DB_INFO) if not args.private else DBManager(DB_INFO_P)
    
    # create_binance_table(manager, args.name)
    # print(args.ticker, args.startdate, args.future)
    # input_data = get_kline_data_ccxt(ticker=args.ticker, start_dt=args.startdate, is_future=args.future)
    # manager.insert_all(args.name, input_data)

    
    for ticker in ['BTC', 'ETH']:
        for b in [True, False]:
            f = "_future" if b else ""
            daily_btc = get_kline_data_ccxt(f'{ticker}/USDT', '2020-01-01', '1d', b)
            df = pd.DataFrame(daily_btc, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.iloc[::-1].reset_index(drop=True)
            df.to_csv(f'binance_1d_{ticker}USDT{f}.csv', index=False)
