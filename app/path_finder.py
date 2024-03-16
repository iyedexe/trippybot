import time
from utils import secure_get
from app.financial_objects import CoinPair, Order, Way

class PathFinder:
    def __init__(self):
        pass

    def bench_fastest_endpoint(self):
        binance_base_endpoints = [
            "https://api.binance.com",
            "https://api-gcp.binance.com",
            "https://api1.binance.com",
            "https://api2.binance.com",
            "https://api3.binance.com",
            "https://api4.binance.com",
        ]
        min_time_delta = 10000
        for endpoint in binance_base_endpoints:     
            call_time = time.time()*1000
            response = secure_get(f"{endpoint}/api/v3/time")
            if response.status_code != 200:
                continue
            time_delta = float(response.json()['serverTime']) - float(call_time)
            if min_time_delta >= time_delta:
                min_time_delta = time_delta
                binance_base_endpoint = endpoint
            print(f"Timedelta for {endpoint}= [{time_delta}]")
        return binance_base_endpoint

    def get_pairs_list(self, endpoint):
        response = secure_get(f"{endpoint}/api/v3/exchangeInfo")
        if response.status_code != 200:
            return []
        possible_pairs = [CoinPair(symbol["baseAsset"], symbol["quoteAsset"]) for symbol in response.json().get("symbols") if symbol["status"] == "TRADING"]
        #logger how much possible pairs
        return possible_pairs

    #connect to exchange and get list of pairs
    def get_possible_paths(self, start_coin, inter_coin, final_coin):
        steps = [ 
            [Order(CoinPair(inter_coin,start_coin), Way.BUY) , Order(CoinPair(start_coin,inter_coin), Way.SELL)],
            [Order(CoinPair(final_coin,inter_coin), Way.BUY) , Order(CoinPair(inter_coin,final_coin), Way.SELL)],
            [Order(CoinPair(start_coin,final_coin), Way.BUY) , Order(CoinPair(final_coin,start_coin), Way.SELL)]
        ]
        ways = [
            [steps[0][0], steps[1][0], steps[2][0]],
            [steps[0][0], steps[1][0], steps[2][1]],
            [steps[0][0], steps[1][1], steps[2][0]],
            [steps[0][0], steps[1][1], steps[2][1]],
            [steps[0][1], steps[1][0], steps[2][0]],
            [steps[0][1], steps[1][0], steps[2][1]],
            [steps[0][1], steps[1][1], steps[2][0]],
            [steps[0][1], steps[1][1], steps[2][1]],
        ]
        #logger how much possible paths
        return ways
            
    def is_path_real(self, path, pairs_universe):
        path_pairs = [Order._pair for Order in path]
        for pair in path_pairs:
            if pair not in pairs_universe:
                return False
        return True

    def init(self):
        bnb_endpoint = self.bench_fastest_endpoint()
        pairs_universe = self.get_pairs_list(bnb_endpoint)
        possible_paths = self.get_possible_paths('ETH', 'BTC', 'BNB')
        realistic_paths = [path for path in possible_paths if self.is_path_real(path, pairs_universe)]
        print(f"possible arbitrage paths : \n{realistic_paths}")
        return realistic_paths
