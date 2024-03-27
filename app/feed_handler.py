import websocket
import json
import multiprocessing
from strategy import ArbitrageStrategy
from utils import init_logger

# If you like to run in debug mode
websocket.enableTrace(False)
log = init_logger('FeedHandler')

class FeedHandler:
    def __init__(self, config, ticker_list):
        self._config = config
        market_connection = config['FEED_HANDLER']['market_connection']
        self._websocket_endpoint = config[market_connection]['websocket_endpoint']

        self.ticker_list = ticker_list
        self.data = {}
  
    def on_open(self, wsapp):
        log.info("connection open")

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
            # log.debug(f"receiverd frame : {message}")
            self.store_message(message)
            signal = self.strat.check_opportunity(self.data)
            if signal is not None:
                self.q.put(signal)
        except Exception as e:
            log.exception(f"exception : {e}")
            
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

    def run(self, q: multiprocessing.Queue, strat : ArbitrageStrategy):
        self.q = q
        self.strat = strat
        wsapp = websocket.WebSocketApp(f"{self._websocket_endpoint}/stream?streams={'/'.join([f'{ticker.lower()}@bookTicker' for ticker in self.ticker_list])}",
                                        on_message=self.on_message,
                                        on_open=self.on_open,
                                        on_error=self.on_error,
                                        on_ping=self.on_ping,
                                        on_pong=self.on_pong)
        wsapp.run_forever()
        