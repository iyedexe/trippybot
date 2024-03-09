import websocket
import json
import multiprocessing
from strat import ArbitrageStrategy
from fin import Transaction, Way, CoinPair

# If you like to run in debug mode
websocket.enableTrace(False)

class Fluxer:
    def __init__(self, ticker_list, strat : ArbitrageStrategy):
        self.ticker_list = ticker_list
        self.data = {}
        self.strat = strat
        
        subscription_list =  [f"{ticker.lower()}@bookTicker" for ticker in ticker_list]
        self.binance_socket = f"wss://stream.binance.com:9443/stream?streams={'/'.join(subscription_list)}"
  
    def on_open(self, wsapp):
        print("connection open")

    def store_message(self, message):
        dict_message = json.loads(message)
        data = dict_message.get("data")
        if data is None:
            return
        ticker = data.get("s")
        if ticker is None or ticker not in self.ticker_list:
            return
        self.data[ticker] = data

    def on_message(self, wsapp, message):
        try:            
            # print(f"receiverd : {message}")
            self.store_message(message)
            self.strat.check_opportunity(self.data)
            # self.q.push(signal)
        except Exception as e:
            print(f"exception : {e}")
            
    def on_error(wsapp, error):
        print(error)

    def on_close(self, wsapp, close_status_code, close_msg):
        print("Connection close")
        print(close_status_code)
        print(close_msg)

    def on_ping(self, wsapp, message):
        print("received ping from server")

    def on_pong(self, wsapp, message):
        print("received pong from server")

    def run(self, q: multiprocessing.Queue):
        self.q = q
        wsapp = websocket.WebSocketApp(self.binance_socket,
                                        on_message=self.on_message,
                                        on_open=self.on_open,
                                        on_error=self.on_error,
                                        on_ping=self.on_ping,
                                        on_pong=self.on_pong)
        wsapp.run_forever()


if __name__ == '__main__':
    import requests
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    
    print(requests.get(url).json())
    input()
    ticker_list = ["ETHBTC", "BNBBTC", "BNBETH"]
    
    q = multiprocessing.Queue()
    path = [
        Transaction(CoinPair("ETH", "BTC"), Way.SELL),
        Transaction(CoinPair("BNB", "BTC"), Way.BUY),
        Transaction(CoinPair("BNB", "ETH"), Way.SELL),
    ]
    strat = ArbitrageStrategy(path)
    fluxer = Fluxer(ticker_list, strat)
    fluxer = multiprocessing.Process(name='fluxer', target=fluxer.run, args=(q,))
    fluxer.start()


