# import telegram
import signal
import asyncio 
import multiprocessing
import websocket
import json
from urllib.parse import urlencode
import threading
import uuid
import logging
import configparser
import time
from colorlog import ColoredFormatter

from financial_objects import Order, Signal, Way, CoinPair
from utils import hashing, get_timestamp, signal_handler, CustomFormatter

signal.signal(signal.SIGINT, signal_handler)

# log = logging.getlog('OrderHandler')
# log.setLevel(logging.DEBUG)
# ch = logging.StreamHandler()
# ch.setLevel(logging.DEBUG)
# # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# ch.setFormatter(CustomFormatter())
# log.addHandler(ch)

LOG_LEVEL = logging.DEBUG
LOGFORMAT = "%(log_color)s%(asctime)s%(reset)s | %(log_color)s%(name)s%(reset)s | %(log_color)s%(levelname)s%(reset)s | %(message)s"
logging.root.setLevel(LOG_LEVEL)
formatter = ColoredFormatter(LOGFORMAT)
stream = logging.StreamHandler()
stream.setLevel(LOG_LEVEL)
stream.setFormatter(formatter)
log = logging.getLogger('OrderHandler')
log.setLevel(LOG_LEVEL)
log.addHandler(stream)

class OrderHandler:
    def __init__(self, config):
        self._config = config
        market_connection = config['ORDER_HANDLER']['market_connection']

        # self._telegram_api_key = config['TELEGRAM']['api_key']
        # self._telegram_user_id = config['TELEGRAM']['user_id']

        self._websocket_endpoint = config[market_connection]['websocket_endpoint']
        self._binance_api_key = config[market_connection]['api_key']
        self._binance_key_secret = config[market_connection]['key_secret']

        self._conditions = {}
        self._message_response = {}
        self._bot = None
        
    def send_message(self, message):
        if self._bot is None:
            self._bot = telegram.Bot(token=self._telegram_api_key)

        asyncio.run(self._bot.send_message(chat_id=self._telegram_user_id, text=message))      

    async def process_signal(self, signal: Signal, wsapp):
        orders_list = signal.get_orders_list()
        # self.send_message(f"Signal received, Theo unitairy pnl = {signal.get_theo_pnl()}\n , Description = {signal.get_description()}")
        log.info(f"Signal received:\n"
              "\tTheo unitairy pnl = [{signal.get_theo_pnl()}],\n" 
              "\tDescription = [{signal.get_description()}]")

        for order in orders_list:

            pair = order.get_pair()
            if order.get_way() == Way.BUY:
                starting_coin = pair.get_quote_currency()
            elif order.get_way() == Way.SELL:
                starting_coin = pair.get_base_currency()

            balance = await self.get_balance(wsapp, starting_coin)
            log.info(f'Current balance of {starting_coin} : {balance}')

    async def get_balance(self, wsapp, asset):
        message_id = str(uuid.uuid4())
        self._conditions[message_id] = asyncio.Event()

        message_to_server = json.dumps(self.get_account_status(message_id))
        log.critical(f"Sending message to server: {message_to_server}")
        wsapp.send(message_to_server)
        log.critical(f"Waiting for message to return : {message_id}")
        await self._conditions[message_id].wait()
        response = self._message_response[message_id]
        return response


    def get_account_status(self, message_id):
        timestamp = get_timestamp()
        payload = {
            "apiKey": self._binance_api_key,
            "timestamp": timestamp,
        }
        signature = hashing(urlencode(payload), self._binance_key_secret)
        payload['signature'] = signature

        return {
            "id": message_id,
            "method": "account.status",
            "params": payload
        }
    # def place_order(self, wsapp, order:Order):
    #     message_to_server = json.dumps(self.place_order_message(order))
    #     log.debug(f"Sending message to server: {message_to_server}")
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
        log.info('WS connection opened ..')

        while True:
            log.info('Listening to signals queue ..')
            signal = self.q.get()
            log.info('Caught new signal ..')
            if signal is None:
                break
            asyncio.run(self.process_signal(signal, wsapp))
            

    def on_message(self, wsapp, message):
        log.info(f"Receiving message from server: {message}")
        message_json = json.loads(message)
        message_id = message_json.get('id')
        if message_id is None:
            log.error('Message received with no id : {message}')
            return
        self._message_response[message_id] = message_json
        self._conditions[message_id].set()

        log.info(message)

    def on_error(self, wsapp, error):
        log.error(error)

    def on_close(self, wsapp, close_status_code, close_msg):
        log.warning("Connection close")
        log.info(close_status_code)
        log.info(close_msg)

    def on_ping(self, wsapp, message):
        log.info("received ping from server")

    def on_pong(self, wsapp, message):
        log.info("received pong from server")

    def run(self, q :multiprocessing.Queue):
        self.q = q
        log.info('Order handler running ..')
        wsapp = websocket.WebSocketApp(self._websocket_endpoint,
									on_message=self.on_message,
									on_open=self.on_open,
									on_error=self.on_error,
									on_ping=self.on_ping,
									on_pong=self.on_pong)
        wsapp.run_forever()

def main():
    log.info("Order Handler starting main process")

    config = configparser.ConfigParser()
    config.read('config.ini')

    

    q = multiprocessing.Queue()
    oh = OrderHandler(config)
    ohp = multiprocessing.Process(name='OrderHandler', target=oh.run, args=(q,))
    ohp.start()
    path = [

        Order(CoinPair("ETH", "BTC"), Way.SELL),
        Order(CoinPair("BNB", "BTC"), Way.BUY),
        Order(CoinPair("BNB", "ETH"), Way.SELL),
    ]
    signal = Signal(
        path,
        "TESTING SIGNAL",
        1
    )
    log.info("Sleeping 3s before launching signal")
    time.sleep(3)
    q.put(signal)
    log.info("Signal launched")
    ohp.join()


if __name__ == '__main__':
    main()
