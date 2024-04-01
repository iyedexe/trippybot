import signal
import websocket
import json
import multiprocessing
from utils import init_logger, signal_handler

# If you like to run in debug mode
websocket.enableTrace(False)
signal.signal(signal.SIGINT, signal_handler)
log = init_logger('FeedHandler')

class FeedHandler:
    def __init__(self, config, symbol_list):
        self._config = config
        market_connection = config['FEED_HANDLER']['market_connection']
        self._websocket_endpoint = config[market_connection]['websocket_endpoint']

        self.symbol_list = symbol_list
        self.data = {}
  
    def on_open(self, wsapp):
        log.info("WS connection opened ..")

    def store_message(self, message):
        dict_message = json.loads(message)
        data = dict_message.get("data")
        if data is None:
            return
        symbol = data.get("s")
        if symbol is None or symbol not in self.symbol_list:
            return
        self.data[symbol] = data

    def on_message(self, wsapp, message):
        try:            
            # log.debug(f"receiverd frame : {message}")
            self.store_message(message)
            self.q.put(self.data)
        except Exception as e:
            log.error(f"Exception on message : {message}")
            log.exception(f"{e}")
            
    def on_error(wsapp, error):
        log.info(error)

    def on_close(self, wsapp, close_status_code, close_msg):
        log.info("Connection close")
        log.info(close_status_code)
        log.info(close_msg)

    def on_ping(self, wsapp, message):
        log.info("received ping from server")

    def on_pong(self, wsapp, message):
        log.info("received pong from server")

    def run(self, q: multiprocessing.Queue):
        self.q = q
        log.info('Feed handler running ..')
        subscription_subject = '/'.join([f"{symbol.lower()}@bookTicker" for symbol in self.symbol_list])
        log.info(f"Subscribing to streams : {subscription_subject}")
        wsapp = websocket.WebSocketApp(f"{self._websocket_endpoint}/stream?streams={subscription_subject}",
                                        on_message=self.on_message,
                                        on_open=self.on_open,
                                        on_error=self.on_error,
                                        on_ping=self.on_ping,
                                        on_pong=self.on_pong)
        wsapp.run_forever()
        