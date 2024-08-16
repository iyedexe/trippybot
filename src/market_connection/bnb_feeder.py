import logging
import asyncio
import time
import configparser
import signal
import aiohttp
import json
import multiprocessing
import datetime

from collections import defaultdict 

from src.common.utils import init_logger, signal_handler
from src.common.financial_objects import CandleStickMD, TickMD, MarketDataFrame

signal.signal(signal.SIGINT, signal_handler)
log = init_logger('Feeder')


class IBNBFeeder:
    """
    Generic async class for market data server
    Uses websocket to subscribe to binance MD.
    pushes updates on multiprocess queue
    """
    def __init__(self, config):
        market_connection = config['FEEDER']['market_connection']
        self.logging_interval = int(config['FEEDER'].get('logging_interval', 60))
        self._websocket_endpoint = config[market_connection]['websocket_endpoint']
        self.number_of_updates = defaultdict(int)
        self.prev_time = time.time()
  
    def create_md_frame(self, message) -> MarketDataFrame:
        #Method to be overriden per feeder on text to data parse
        pass

    def get_stream_uri(symbol_list):
        #Method to be overriden per feeder to generate wss uri subscription
        pass 

    def subscribe(self, symbol_list: list[str]):
        self.symbol_list = symbol_list

    def log_stats_info(self, frame):
        """
        Method for stats collection and periodic logging.
        Logs num Updates per symbol every logging_interval seconds
        """
        self.number_of_updates[frame.get_symbol()] +=1
        current_time = time.time()
        if current_time > self.prev_time + self.logging_interval:
            self.prev_time = current_time
            log.info(f"Listening to [{len(self.symbol_list)}] symbols on binance")
            for symbol in self.symbol_list:
                log.info(f"Number of updates on [{symbol}]=[{self.number_of_updates.get(symbol)}]")
        
    def on_message(self, message):
        try:            
            frame = self.create_md_frame(message)
            self.log_stats_info(frame)            
            self.q.put(frame)
        except Exception as e:
            log.error(f"Exception on message : {message}")
            log.exception(f"{e}")

    async def listen_socket(self):
        while True:
            wsMessage = await self.ws.receive()
            log.debug(f'Got message on ws: {wsMessage}')
            if wsMessage.type == aiohttp.WSMsgType.ERROR:
                log.critical(f"Error message received : [{wsMessage}]")
                continue
            if wsMessage.type == aiohttp.WSMsgType.TEXT:
                self.on_message(wsMessage.data) 

    async def run_(self, q: multiprocessing.Queue):
        self.q = q
        log.info('Feed handler running ..')
        websocket_uri = self.get_stream_uri(self.symbol_list)
        self.session = aiohttp.ClientSession()
        self.ws = await self.session.ws_connect(f"{self._websocket_endpoint}/{websocket_uri}",
                                                max_msg_size = 10 * 1024 * 1024)
        log.info('Binance client WS connection established')
        await self.listen_socket()

    def run(self, q: multiprocessing.Queue):
        asyncio.run(self.run_(q))

class CandleStickBNBFeeder(IBNBFeeder):
    def create_md_frame(self, message) -> CandleStickMD:
        dict_message = json.loads(message)
        data = dict_message.get("data")        
        return CandleStickMD(
            symbol= data.get("s"),
            open = data.get("k").get("o"),
            close= data.get("k").get("c"),
            high= data.get("k").get("h"),
            low= data.get("k").get("l"),
            local_ts = datetime.datetime.now(), #localTimestamp on reception
            market_ts= None, #Market timestamp
        )

    def get_stream_uri(symbol_list):
        subscription_subject = '/'.join([f"{symbol.lower()}@kline_1s" for symbol in symbol_list])
        log.info(f"Subscribing to streams : {subscription_subject}")
        websocket_uri = f"stream?streams={subscription_subject}"
        return websocket_uri


class TickBNBFeeder(IBNBFeeder):
    def create_md_frame(self, message) -> TickMD:
        dict_message = json.loads(message)
        data = dict_message.get("data")        
        return TickMD(
            symbol= data.get("s"),
            bid = data.get("b"),
            bid_qty= data.get("B"),
            ask= data.get("a"),
            ask_qty= data.get("A"),
            local_ts = datetime.datetime.now(), #localTimestamp on reception
            market_ts= None, #Market timestamp
        )

    def get_stream_uri(symbol_list):
        subscription_subject = '/'.join([f"{symbol.lower()}@bookTicker" for symbol in symbol_list])
        log.info(f"Subscribing to streams : {subscription_subject}")
        websocket_uri = f"stream?streams={subscription_subject}"
        return websocket_uri


def main():
    config = configparser.ConfigParser()
    config.read('config.ini')

    logging.root.setLevel(logging.DEBUG)
    fh = CandleStickBNBFeeder(config, ["BTCUSDT", "TRXUSDT"])
    q = multiprocessing.Queue()
    fh.run(q)

if __name__ == "__main__":
    main()