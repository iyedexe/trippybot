import websocket
import json
import multiprocessing

# If you like to run in debug mode
websocket.enableTrace(False)

class Fluxer:
    def __init__(self, ticker_list):
        self.ticker_list = ticker_list

    def subscribe_coins_message(self, ticker_list):
        return {
        "id": "1",
        "method": "ticker.book",
        "params": {
            "symbols": ticker_list
        }
        }
    
    def on_open(self, wsapp):
        print("connection open")

        message_to_server = json.dumps(self.subscribe_coins_message(self.ticker_list))

        print("sending message to server:")
        print(message_to_server)
        wsapp.send(message_to_server)

    def on_message(self, wsapp, message):
        print("Receiving message from server:")
        print(message)
        # on_open(self, wsapp)

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
        wsapp = websocket.WebSocketApp("wss://ws-api.binance.com/ws-api/v3",
                                        on_message=self.on_message,
                                        on_open=self.on_open,
                                        on_error=self.on_error,
                                        on_ping=self.on_ping,
                                        on_pong=self.on_pong)
        wsapp.run_forever()
