import os 
import json
import requests  
import argparse
import pandas as pd
import logging

BASE_URL = "https://api.glassnode.com"
END_ENDPOINT = "/v2/metrics/endpoints"
REQ_URL = BASE_URL + END_ENDPOINT
HEADER = {
    "Cookie": """_ga_TQZT4J2QD5=GS1.1.1727868545.1.1.1727869089.0.0.0; _gcl_au=1.1.188069838.1728295674; _hjSessionUser_1425107=eyJpZCI6ImNkYTBkMGNjLTY1YTAtNWQwNC05NTgzLTk4ODM0YTY0Njc2NSIsImNyZWF0ZWQiOjE3MjgyOTU2NzcyMTQsImV4aXN0aW5nIjp0cnVlfQ==; _hjSessionUser_3114558=eyJpZCI6ImUyNWU4ZGIwLWE5MDctNTJkYi04Nzg5LTYzOGVhNzM2Y2RiZCIsImNyZWF0ZWQiOjE3MjgyOTU2NjAxMDAsImV4aXN0aW5nIjp0cnVlfQ==; crisp-client%2Fsession%2Fa43d4e77-dbfa-47e6-8cb5-b4c770314944=session_b89cac81-0777-4f6d-89ac-31c55c643b7f; _ga_HJE430PTJT=GS1.1.1728479977.1.1.1728480329.60.0.0; _gcl_gs=2.1.k1$i1728801940$u204686034; _gcl_aw=GCL.1728801944.CjwKCAjwvKi4BhABEiwAH2gcw4Hw0jaV9tz_Ol5jZ9t3Gx0FWOlRZYz_Mr9bYfR9k8H2-T2O41H-VBoCvP4QAvD_BwE; _gac_UA-129287447-1=1.1728801945.CjwKCAjwvKi4BhABEiwAH2gcw4Hw0jaV9tz_Ol5jZ9t3Gx0FWOlRZYz_Mr9bYfR9k8H2-T2O41H-VBoCvP4QAvD_BwE; _ga_8MGXPNL6MF=GS1.1.1730988533.4.0.1730988535.58.0.1368699488; _gid=GA1.2.24296981.1730988551; _hjSession_1425107=eyJpZCI6ImEwYjc1NDU5LTgyNzItNDNmYi05ZWRlLTViOWMwMWNkYWYyNyIsImMiOjE3MzA5ODg1NTI5MjcsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=; ajs_user_id=cus_VayYNBDNvD0g5wLj; ajs_anonymous_id=51f56b44-5107-4f9f-b6c3-3846e4e4c4a0; _ga_M9YVRZCN8G=GS1.1.1730988551.14.1.1730988741.0.0.0; _ga_MT5MWT6847=GS1.1.1730988551.14.1.1730988741.38.0.0; _s=MTczMDk4ODczOXx5TzdaYm5pa2VRUGJXVUxDdUNZQk1JeWlnSUUyeVE0LW84WjdaN1Nxb05lODVOeld4SG51YlNnRlFJYzhfaGc9fDeBp00hvw53-Ma5CJO4kVBz2C6b0ZBniA47zC8MXMfp; _gat_gtag_UA_129287447_3=1; _ga_YYWW6JR31S=GS1.1.1730988721.8.1.1730988920.0.0.0; _ga=GA1.1.1724244220.1727868546"""
}

# Setup logging
logging.basicConfig(level=logging.INFO)


def setup_workdir(workdir):
    ## Directory setting.
    if workdir == "":
        print(f"Working directory is not set. It will be current directory : {os.getcwd()}")
    elif not os.path.exists(workdir):
        raise ValueError("Invalid working directory.")
    if not os.path.exists(os.path.join(workdir, "glassnode")):
        os.mkdir(os.path.join(workdir, "glassnode"))
        

def fetch_endpoints():
    ## Get endpoints to requests.
    logging.info("ENDPOINT REQUESTS ...")
    resp = requests.get(REQ_URL, headers=HEADER)
    if resp.status_code != 200:
        logging.error("FAIL. exit program.")
        raise Exception("Bad Requests.")
    logging.info("Done.")
    return json.loads(resp.content)


def process_endpoints(endpoint_list, workdir):
    ## Start Requests.
    for i, endp in enumerate(endpoint_list):
        
        # Check if endpoint is available for basic user
        if endp['tier'] != 1:
            continue
        
        # Check if endpoint has available data for BTC or ETH 
        assets = [asset for asset in endp['assets'] if asset['symbol'] == "BTC" or asset['symbol'] == "ETH"]
        if len(assets) == 0:
            continue
        
        # Check if there is available time interval for requests.
        if len(endp['resolutions']) < 1:
            continue
        
        endp_name = endp['path'].split("/")[-1]
        for asset in assets:
            ticker = asset['symbol']
            
            # resolution = endp['resolutions'][1]  # set the tightest interval
            resolution = "24h"
            
            url = BASE_URL + endp['path'] + f"?a={ticker}&i={resolution}"
            
            file_name = f"{endp_name}_{ticker}.json"
            file_path = os.path.join(workdir, os.path.join("glassnode", file_name))
            
            # if file_name in ALREADY_REQS:
            #     print(f"file is aleady exists in {file_path}")
            #     continue
            
            resp = requests.get(url, headers= HEADER)

            if resp.status_code != 200:
                print(f"REQ ERROR CODE {resp.status_code}. {endp['path']} / ASSET={ticker}")
                continue
            
            with open(file_path, "w") as f:
                json.dump(resp.text, f)
                print(f"REQ SUCCESS; {endp_name} API FOR ASSET={ticker}; SAVED AT {file_path}")
                

def agg_json(data_dir ='glassnode', is_btc=True):
    """aggregate json files to dataframe."""
    
    btc_glass_node = os.listdir(data_dir)
    eth_glass_node = []

    ## file path split - BTC / ETH
    for i, file in enumerate(btc_glass_node):
        if file.find("ETH") != -1:
            eth_glass_node.append(btc_glass_node.pop(i))

    def get_df(path):
        names = path.split('\\')[-1].split('_')[:-1]
        name = "_".join(names)
        with open(path, "r") as f: 
            json_data = json.loads(json.load(f))
            df = pd.DataFrame(json_data)
            df.columns = ['time', name]
            return df.set_index('time')

    glass_node = btc_glass_node if is_btc else eth_glass_node
    glass_path = [os.path.join(data_dir, path) for path in glass_node]
    df = pd.concat(map(get_df, glass_path), axis=1)
    return df


def agg_df(is_btc=True):
    """aggregate on-chain data and close data"""
    onchain_df = agg_json(is_btc=is_btc)
    onchain_df.index = pd.to_datetime(onchain_df.index, unit="s")

    ticker = "BTC" if is_btc else "ETH"
    close_df = pd.read_csv(f"binance_1m_{ticker}USDT.csv")
    close_df = close_df[['timestamp', 'close']].set_index('timestamp').copy()
    close_df.index = pd.to_datetime(close_df.index, unit="ms")

    close_df = close_df.resample('1d').last()
    final_df = close_df.merge(onchain_df, how='left', left_index=True, right_index=True)
    return final_df

def save_dataframes(workdir):
    """save dataframes to csv files."""
    btc_df = agg_df(is_btc=True)
    eth_df = agg_df(is_btc=False)

    btc_df.drop('pi_cycle_top', axis=1, inplace=True)
    eth_df.drop('pi_cycle_top', axis=1, inplace=True)

    btc_df.to_csv(os.path.join(workdir, os.path.join("glassnode", 'glassnode_BTC_tier1.csv')))
    eth_df.to_csv(os.path.join(workdir, os.path.join("glassnode", 'glassnode_ETH_tier1.csv')))

def main(workdir):
    setup_workdir(workdir)
    endpoint_list = fetch_endpoints()
    process_endpoints(endpoint_list, workdir)
    save_dataframes(workdir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--workdir", default="")
    args = parser.parse_args()
    
    main(args.workdir)
