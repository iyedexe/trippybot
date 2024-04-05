import signal
import json
import multiprocessing
from utils import init_logger, signal_handler
from financial_objects import MarketDataFrame
import aiohttp

signal.signal(signal.SIGINT, signal_handler)
log = init_logger('FeedHandler')

class FeedHandler:
    def __init__(self, config, symbol_list):
        self._config = config
        market_connection = config['FEED_HANDLER']['market_connection']
        self._websocket_endpoint = config[market_connection]['websocket_endpoint']

        self.symbol_list = symbol_list
  
    def create_md_frame(self, message):
        dict_message = json.loads(message)
        data = dict_message.get("data")
        return MarketDataFrame(
            symbol= data.get("s"),
            bid = data.get("b"),
            bid_qty= data.get("B"),
            ask= data.get("a"),
            ask_qty= data.get("A") 
        )

    def on_message(self, message):
        try:            
            frame = self.create_md_frame(message)
            self.q.put(frame)
        except Exception as e:
            log.error(f"Exception on message : {message}")
            log.exception(f"{e}")

    async def listen_socket(self):
        while True:
            wsMessage = await self.ws.receive()
            # log.debug(f'Got message on ws: {wsMessage}')
            if wsMessage.type == aiohttp.WSMsgType.ERROR:
                log.critical(f"Error message received : [{wsMessage}]")
                return None
            if wsMessage.type == aiohttp.WSMsgType.TEXT:
                self.on_message(wsMessage.data) 
            
    async def run(self, q: multiprocessing.Queue):
        self.q = q
        log.info('Feed handler running ..')
        subscription_subject = '/'.join([f"{symbol.lower()}@bookTicker" for symbol in self.symbol_list])
        log.info(f"Subscribing to streams : {subscription_subject}")
        self.session = aiohttp.ClientSession()
        self.ws = await self.session.ws_connect(f"{self._websocket_endpoint}/stream?streams={subscription_subject}",
                                                max_msg_size = 10 * 1024 * 1024)
        log.info(f'Binance client WS connection established')
        await self.listen_socket()

