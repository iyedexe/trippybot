import websocket
import json
import multiprocessing

# If you like to run in debug mode
websocket.enableTrace(False)

class Fluxer:
    def __init__(self, ticker_list):
        self.ticker_list = ticker_list
        subscription_list =  [f"{ticker.lower()}@bookTicker" for ticker in ticker_list]
        self.binance_socket = f"wss://stream.binance.com:9443/stream?streams={'/'.join(subscription_list)}"
  
    def on_open(self, wsapp):
        print("connection open")

    def on_message(self, wsapp, message):
        print("Receiving message from server:")
        print(message)

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
        wsapp = websocket.WebSocketApp(self.binance_socket,
                                        on_message=self.on_message,
                                        on_open=self.on_open,
                                        on_error=self.on_error,
                                        on_ping=self.on_ping,
                                        on_pong=self.on_pong)
        wsapp.run_forever()


if __name__ == '__main__':
    ticker_list = ["ETHBTC", "BNBBTC", "BNBETH"]
    fluxer = Fluxer(ticker_list)
    q = multiprocessing.Queue()
    fluxer = multiprocessing.Process(name='fluxer', target=fluxer.run, args=(q,))
    fluxer.start()


