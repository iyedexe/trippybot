import websocket
import json
import multiprocessing
from app.strategy import ArbitrageStrategy

# If you like to run in debug mode
websocket.enableTrace(False)

class FeedHandler:
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
            print(f"receiverd : {message}")
            self.store_message(message)
            signal = self.strat.check_opportunity(self.data)
            if signal is not None:
                self.q.put(signal)
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
        