from datetime import datetime 
from data.enums import *

def get_path_subset(dir_list, start_dt, end_dt) -> list:
    """
    load subset w.r.t start_date from dir_list
    """
    subpaths = []
    for filepath in dir_list:
        inpath_date = datetime.strptime(filepath.split(".")[0][-10:], "%Y-%m-%d")
        if inpath_date >= datetime.strptime(start_dt, "%Y-%m-%d") and inpath_date <= datetime.strptime(end_dt, "%Y-%m-%d"):
            subpaths.append(filepath)
    return subpaths

def get_ticker_path(exchange, market, ticker):
    base_path = PATH_CONFIG[f"{exchange}_{market}_trades"]
    return os.path.join(base_path, ticker)