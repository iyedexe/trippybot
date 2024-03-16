import telegram
import asyncio 
import multiprocessing
import websocket
import json
from urllib.parse import urlencode

from app.financial_objects import Order
from app.utils import hashing, get_timestamp

class OrderHandler:
    def __init__(self, config):
        self._config = config
        self._telegram_api_key = config['TELEGRAM']['api_key']
        self._telegram_user_id = config['TELEGRAM']['user_id']

        self._binance_api_key = config['BINANCE']['api_key']
        self._binance_api_secret = config['TELEGRAM']['api_secret']

        self._bot = None
        
    def send_message(self, message):
        if self._bot is None:
            self._bot = telegram.Bot(token=self._telegram_api_key)

        asyncio.run(self._bot.send_message(chat_id=self._telegram_user_id, text=message))      

    def process_signal(self, signal, wsapp):
        orders_list = signal.get_orders()
        self.send_message(f"Signal received, Theo unitairy pnl = {signal.theo_pnl}\n , Description = {signal.description}")

        for order in orders_list:
            message_to_server = json.dumps(self.place_order_message(order))
            print("sending message to server:")
            print(message_to_server)
            wsapp.send(message_to_server)

    def place_order_message(self, order: Order):
        timestamp = get_timestamp()
        payload = {
            "symbol": order.get_symbol(),
            "side": order.get_side(),
            "type": order.get_order_type(),
            "quantity": order.get_quantity(),
            "apiKey": self._binance_api_key,
            "timestamp": timestamp,
        }
        signature = hashing(urlencode(payload), self._binance_api_secret)
        payload['signature'] = signature

        return {
            "id": "56374a46-3061-486b-a311-99ee972eb648",
            "method": "order.place",
            "params": payload
        }

    def on_open(self, wsapp):
        while True:
            signal = self.q.get()
            if signal is None:
                break
            self.process_signal(signal, wsapp)

    def on_message(wsapp, message):
        print("Receiving message from server:")
        print(message)

    def on_error(wsapp, error):
        print(error)

    def on_close(wsapp, close_status_code, close_msg):
        print("Connection close")
        print(close_status_code)
        print(close_msg)

    def on_ping(wsapp, message):
        print("received ping from server")

    def on_pong(wsapp, message):
        print("received pong from server")

    def run(self, q :multiprocessing.Queue):
        self.q = q
        wsapp = websocket.WebSocketApp("wss://ws-api.binance.com/ws-api/v3",
									on_message=self.on_message,
									on_open=self.on_open,
									on_error=self.on_error,
									on_ping=self.on_ping,
									on_pong=self.on_pong)
        wsapp.run_forever()