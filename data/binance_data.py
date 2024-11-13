from datetime import datetime, timezone
import ccxt

CONFIG = {
    "apikey": "KQqKnPDa9ame2TC0UyjJPQ5Ml6FX1GkjkbP3M4twMNJdQA2b9Ap3eAiCfwuDWiIb",
    "secrete_key": "ZjeTlmlW42ptXJf5YuZYvnAInRrEonVekuDOu0DyUPFR4wlml4WgbwbMqdjmzNtJ",
}

def create_binance_table(manager, table_name):
    """
    TABLE 은 아래와 같이 구성

    CREATE TABLE <table_name> (
        timestamp BIGINT NOT NULL,     -- UNIX 타임스탬프 (정수형)
        open FLOAT,                    -- 시가 (부동 소수점)
        high FLOAT,                    -- 고가 (부동 소수점)
        low FLOAT,                     -- 저가 (부동 소수점)
        close FLOAT,                   -- 종가 (부동 소수점)
        volume FLOAT,                  -- 거래량 (부동 소수점)
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, -- 업데이트 시간
        PRIMARY KEY (timestamp)        -- 타임스탬프를 기본 키로 설정
    );
    
    table_name은 아래와 같은 형식을 따르길
    '<거래소>_<nominator>_<denominator>'
    
    Ex) binance_eth_usdt
    """
    
    sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        timestamp BIGINT NOT NULL,
        open FLOAT,
        high FLOAT,
        low FLOAT,
        close FLOAT,
        volume FLOAT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (timestamp)
    );
    """
    manager.execute(sql)
    
    
def get_kline_data_ccxt(ticker, start_dt="2024-09-24", timeframe='1m', is_future=False):
    """
    Args:
        ticker (str): 바이낸스에서 제공하는 티커 심볼 (예: BTC/USDT)
        start_dt (str): "%Y-%m-%d" 형식의 시작 날짜 (UTC-0)
        timeframe (str): 데이터 시간 간격. '1m'(1분봉), '1h'(1시간봉), '1d'(일봉) 지원
        is_future (bool): 선물 데이터 여부

    Returns:
        list: OHLCV 데이터 리스트 (시작일부터 현재까지)
    """
    param_dict = {"options": {"defaultType": "future"}} if is_future else {}
    binance = ccxt.binance(param_dict)
    req_limit = 1000
    since = None
    start_tp = datetime.strptime(start_dt, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    start_tp = int(start_tp.timestamp()) * 1000  # adjust for binance (ms)

    # timeframe에 따른 시간 간격(ms) 설정
    interval_ms = {
        '1m': 60000,
        '1h': 3600000,
        '1d': 86400000
    }
    
    if timeframe not in interval_ms:
        raise ValueError("지원하지 않는 timeframe입니다. '1m', '1h', '1d' 중 하나를 선택하세요.")
    
    interval = interval_ms[timeframe]
    ohlcv_data = []
    
    while True:
        try: 
            ohlcv_temp = binance.fetch_ohlcv(ticker, timeframe=timeframe, since=since, limit=req_limit)
            
            if ohlcv_temp[0][0] < start_tp:
                idx = (start_tp - ohlcv_temp[0][0]) // interval
                ohlcv_data.extend(ohlcv_temp[idx:][::-1])
                break
            
            else:
                ohlcv_data.extend(ohlcv_temp[::-1])
        
            print("REQ SUCCESS.")
            
            since = ohlcv_temp[0][0] - interval * req_limit
            print(f"req_limit: {req_limit}")
            print(f"since: {since}")
        except:
            print(f"ERROR OCCUR at {since}")
            break

    return ohlcv_data
    
if __name__ == "__main__":
    pass