import telegram
import asyncio 
import multiprocessing
import websocket
import json
from urllib.parse import urlencode
import threading
import uuid
import logging
import configparser

from financial_objects import Order, Signal, Way, CoinPair
from utils import hashing, get_timestamp


logger = logging.getLogger(__name__)
c_handler = logging.StreamHandler()
c_handler.setLevel(logging.DEBUG)
c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
logger.addHandler(c_handler)

class OrderHandler:
    def __init__(self, config):
        self._config = config
        self._telegram_api_key = config['TELEGRAM']['api_key']
        self._telegram_user_id = config['TELEGRAM']['user_id']

        self._binance_api_key = config['BINANCE']['api_key']
        self._binance_api_secret = config['TELEGRAM']['api_secret']

        self._conditions = {}
        self._message_response = {}
        self._bot = None
        
    def send_message(self, message):
        if self._bot is None:
            self._bot = telegram.Bot(token=self._telegram_api_key)

        asyncio.run(self._bot.send_message(chat_id=self._telegram_user_id, text=message))      

    def process_signal(self, signal: Signal, wsapp):
        orders_list = signal.get_orders_list()
        self.send_message(f"Signal received, Theo unitairy pnl = {signal.get_theo_pnl()}\n , Description = {signal.get_description()}")

        for order in orders_list:

            pair = order.get_pair()
            if order.get_way() == Way.BUY:
                starting_coin = pair.get_quote_currency()
            elif order.get_way() == Way.SELL:
                starting_coin = pair.get_base_currency()

            balance = self.get_balance(starting_coin, wsapp)
            logger.info(f'Current balance of {starting_coin} : {balance}')

    def get_balance(self, wsapp, asset):
        message_id = uuid.uuid4()
        self._conditions[message_id] = threading.Condition()

        message_to_server = json.dumps(self.get_account_status(message_id))
        logger.debug(f"Sending message to server: {message_to_server}")
        wsapp.send(message_to_server)

        self._conditions[message_id].wait()
        response = self._message_response[message_id]
        return response


    def get_account_status(self, message_id):
        timestamp = get_timestamp()
        payload = {
            "apiKey": self._binance_api_key,
            "timestamp": timestamp,
        }
        signature = hashing(urlencode(payload), self._binance_api_secret)
        payload['signature'] = signature

        return {
            "id": message_id,
            "method": "account.status",
            "params": payload
        }
    # def place_order(self, wsapp, order:Order):
    #     message_to_server = json.dumps(self.place_order_message(order))
    #     logger.debug(f"Sending message to server: {message_to_server}")
    #     wsapp.send(message_to_server)

    # def place_order_message(self, order: Order):
    #     timestamp = get_timestamp()
    #     payload = {
    #         "symbol": order.get_symbol(),
    #         "side": order.get_side(),
    #         "type": order.get_order_type(),
    #         "quantity": order.get_quantity(),
    #         "apiKey": self._binance_api_key,
    #         "timestamp": timestamp,
    #     }
    #     signature = hashing(urlencode(payload), self._binance_api_secret)
    #     payload['signature'] = signature

    #     return {
    #         "id": "56374a46-3061-486b-a311-99ee972eb648",
    #         "method": "order.place",
    #         "params": payload
    #     }

    def on_open(self, wsapp):
        while True:
            signal = self.q.get()
            if signal is None:
                break
            self.process_signal(signal, wsapp)

    def on_message(self, wsapp, message):
        logger.info("Receiving message from server:")
        message_json = json.loads(message)
        message_id = message_json.get('id')
        if message_id is None:
            logger.error('Message received with no id : {message}')
            return
        self._message_response[message_id] = message_json
        self._conditions[message_id].notify()

        print(message)

    def on_error(self, wsapp, error):
        print(error)

    def on_close(self, wsapp, close_status_code, close_msg):
        print("Connection close")
        print(close_status_code)
        print(close_msg)

    def on_ping(self, wsapp, message):
        print("received ping from server")

    def on_pong(self, wsapp, message):
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

def main():
    config = configparser.ConfigParser()
    config.read('config.ini')

    q = multiprocessing.Queue()
    oh = OrderHandler(config)
    ohp = multiprocessing.Process(name='OrderHandler', target=oh.run, args=(q,))
    ohp.start()

    signal = [
        Order(CoinPair("ETH", "BTC"), Way.SELL),
        Order(CoinPair("BNB", "BTC"), Way.BUY),
        Order(CoinPair("BNB", "ETH"), Way.SELL),
    ]
    q.put(signal)

if __name__ == '__main__':
    main()