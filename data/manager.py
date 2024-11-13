## MYSQL Database Manager  
import pymysql

class DBManager:
    """
    Usage:
    
    Example directory:
    - main.py
    - main.ipynb
    - manager.py (this code file)
    
    in 'main.py' or 'main.ipynb' file, you can use DBManager like:
    
    >> import pandas as pd
    >> from manager import DBManager
    >> manager = DBManager()
    >> manager.get_table_names()                                     # DB 내 테이블 이름들 가져오기
    >> data = manager.get_table_data('binance_btc_usdt')             # DB 내 'binance_btc_usdt' 이라는 테이블 값 가져오기  
    >> columns = manager.get_table_column_names('binance_btc_usdt')  # DB 내 'binance_btc_usdt' 이라는 테이블의 열 이름 가져오기  
    >> df = pd.DataFrame(data, columns=columns)                      # 테이블을 데이터프레임 형태로 만들기
    
    """
    
    def __init__(self, DB_INFO):
        self.DB_INFO = DB_INFO
        self.conn = pymysql.connect(**DB_INFO)
        print("Connected.")
        
    def __del__(self):
        self.conn.close()
        
    def execute(self, sql) -> None:
        with self.conn.cursor() as curs:
            curs.execute(sql)
        
    def get_table_names(self):
        with self.conn.cursor() as curs:
            curs.execute(f"SELECT TABLE_NAME FROM information_schema.tables WHERE TABLE_SCHEMA = '{self.DB_INFO['database']}'")
            result = [res[0] for res in curs.fetchall()]
            return result
    
    def get_column_names(self, table_name):
        with self.conn.cursor() as curs:
            curs.execute(f"SELECT COLUMN_NAME FROM information_schema.columns WHERE TABLE_SCHEMA = '{self.DB_INFO['database']}' AND TABLE_NAME = '{table_name}'")
            result = [res[0] for res in curs.fetchall()]
            return result
        
    def select_all(self, sql):
        with self.conn.cursor() as curs:
            curs.execute(sql)
            return curs.fetchall()
    
    def insert_all(self, table_name, input_data:list):
        column_names = self.get_table_column_names(table_name)
        column_names = column_names[:-1] # remove 'updated_at' columns
        
        with self.conn.cursor() as curs:
            col_string = "(" + ", ".join(column_names) +  ")"
            place_holder_string = "(" + ", ".join(["%s"] * len(column_names)) + ")"
            sql = f"""
            INSERT INTO {table_name} {col_string} VALUES {place_holder_string} 
            ON DUPLICATE KEY UPDATE
            open = VALUES(open),
            high = VALUES(high),
            low = VALUES(low),
            close = VALUES(close),
            volume = VALUES(volume);
            """
            
            curs.executemany(sql, input_data)
            self.conn.commit()
        
    def create_table(self, table_name, column_info):
        # mysql 상에서 만드는게 나을 것 같음
        pass 
    
    def get_table_data(self, table_name):
        with self.conn.cursor() as curs:
            curs.execute(f"SELECT * FROM {table_name}")
            return curs.fetchall()
    
    def get_close_data(self, table_name):
        with self.conn.cursor() as curs:
            curs.execute(f"SELECT timestamp, close FROM {table_name}")
            return curs.fetchall()
    
    
if __name__ == "__main__":
    manager = DBManager()
    
    import pandas as pd
    data = manager.get_table_data('binance_btc_usdt')             # DB 내 'binance_btc_usdt' 이라는 테이블 값 가져오기  
    columns = manager.get_table_column_names('binance_btc_usdt')  # DB 내 'binance_btc_usdt' 이라는 테이블의 열 이름 가져오기  
    df = pd.DataFrame(data, columns=columns)  
    df.to_csv("binance_1m_BTCUSDT_f.csv")
    
    data = manager.get_table_data('binance_eth_usdt_f')             # DB 내 'binance_eth_usdt' 이라는 테이블 값 가져오기  
    columns = manager.get_table_column_names('binance_eth_usdt_f')  # DB 내 'binance_eth_usdt' 이라는 테이블의 열 이름 가져오기  
    df = pd.DataFrame(data, columns=columns)  
    df.to_csv("binance_1m_ETHUSDT_f.csv")