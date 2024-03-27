# import telegram
import signal
import asyncio 
import multiprocessing
import aiohttp
import json
import uuid
import configparser
import time
from collections import defaultdict 
from financial_objects import Order, Signal, Way, CoinPair, OrderType
from utils import get_timestamp, signal_handler, init_logger, compute_signature

signal.signal(signal.SIGINT, signal_handler)
log = init_logger('OrderHandler')
STATUS_OK=200

    # def send_message(self, message):
    #     if self._bot is None:
    #         self._bot = telegram.Bot(token=self._telegram_api_key)

    #     asyncio.run(self._bot.send_message(chat_id=self._telegram_user_id, text=message))      


class OrderHandler:
    def __init__(self, config):
        self._config = config
        market_connection = config['ORDER_HANDLER']['market_connection']

        # self._telegram_api_key = config['TELEGRAM']['api_key']
        # self._telegram_user_id = config['TELEGRAM']['user_id']

        self._websocket_endpoint = config[market_connection]['websocket_endpoint']
        self._binance_api_key = config[market_connection]['api_key']
        self._binance_key_secret = config[market_connection]['key_secret']
        self.balance = defaultdict(float)
        self.lot_size = defaultdict(float) 
        self.min_size = defaultdict(float)
        self.max_size = defaultdict(float)


    async def listen_socket(self):
        wsMessage = await self.ws.receive()
        if wsMessage.type == aiohttp.WSMsgType.ERROR:
            log.critical(f"Error message received : [{wsMessage}]")
            return None
        if wsMessage.type == aiohttp.WSMsgType.TEXT:
            return wsMessage.data 

    async def send_command(self, command, *args):
        message_id = str(uuid.uuid4())
        object_res = command(message_id, *args)
        message_to_server = json.dumps(object_res)
        await self.ws.send_str(message_to_server)
        return message_id
    
    async def wait_response(self, message_id):
        log.warning(f'Waiting for response for {message_id}')
        raw_response = await self.listen_socket()
        log.debug(f'raw response : {raw_response}')    
        message_json = json.loads(raw_response)
        rmessage_id = message_json.get('id')
        message_result = message_json.get('result')
        if rmessage_id is None or rmessage_id != message_id:
            raise Exception(f"[BNB] Recieved message id [{rmessage_id}] different than awaited [{message_id}]")
        if message_json.get('status') != STATUS_OK:
            raise Exception(f"[BNB] Market reject, reason [{message_json.get('error')}]")
        return message_result 

    async def process_signal(self, signal: Signal):
        try:
            orders_list = signal.get_orders_list()
            log.info(f"Signal received:\n"
                f"\tTheo unitairy pnl = [{signal.get_theo_pnl()}],\n" 
                f"\tDescription = [{signal.get_description()}]")

            for order in orders_list:

                
                
                await self.execute_order(order)

                log.info(f'Finshed executing order')
        except Exception as e:
            log.critical('An exception occured during signal processing')
            log.exception(e)
            exit(1)
    
    def set_size(self, order: Order):
        pair = order.get_pair()
        if order.get_way() == Way.BUY:
            starting_coin = pair.get_quote_currency()
        elif order.get_way() == Way.SELL:
            starting_coin = pair.get_base_currency()

        if order.get_quantity() == 0:
            qty = self.balance[starting_coin]
        else:
            qty = order.get_quantity()

        self.lot_size[symbol] 
        self.min_size[symbol] = filter_obj['minQty']
        self.max_size[symbol] = filter_obj['maxQty']

        if qty >= self
            

    async def get_balances(self):
        message_id = await self.send_command(self.get_account_status_command)
        account_status = await self.wait_response(message_id)
        
        for asset_balance_obj in account_status.get('balances'):
            self.balance[str(asset_balance_obj['asset'])]=float(asset_balance_obj['free'])
            log.debug(f'Current balance of [{asset_balance_obj["asset"]}] == [{asset_balance_obj["free"]}]')
    
    async def execute_order(self, order:Order):
        if order.getType() != OrderType.MARKET:
            log.error(f'Unhandled order type : {order.getType()}')
        log.info(f'Sending market order way=[{order.get_way()}] symbol=[{order.get_symbol()}] qty=[{order.get_quantity()}]')

        message_id = await self.send_command(self.place_order_command, order)
        exec_response = await self.wait_response(message_id)

        log.info(f'ack_response : {exec_response}')
        log.info('Finished')
    
    async def init_lot_sizes(self):
        log.info('Getting exchange info')
        message_id = await self.send_command(self.get_exchange_info_command)
        exchange_info = await self.wait_response(message_id)
        log.info('Initializing lot sizes')
        for symbol_obj in exchange_info['symbols']:
            symbol = symbol_obj['symbol']
            for filter_obj in symbol_obj['filters']:
                if filter_obj['filterType'] == 'LOT_SIZE':
                    self.lot_size[symbol] = filter_obj['stepSize'] 
                    self.min_size[symbol] = filter_obj['minQty']
                    self.max_size[symbol] = filter_obj['maxQty']

    def get_exchange_info_command(self,message_id):
        return {
            "id": message_id,
            "method": "exchangeInfo"
        }  
            
    def get_account_status_command(self,message_id):
        timestamp = get_timestamp()
        payload = {
            "apiKey": self._binance_api_key,
            "timestamp": timestamp,
        }
        signature = compute_signature(payload, self._binance_key_secret)
        payload['signature'] = signature

        return {
            "id": message_id,
            "method": "account.status",
            "params": payload
        }

    def place_order_command(self, message_id, order: Order):
        log.warning(f'getting in place order command')
        
        timestamp = get_timestamp()
        payload = {
            "apiKey": self._binance_api_key,
            "quantity": f"{order.get_quantity():.8f}",
            "side": str(order.get_way()),
            "symbol": order.get_symbol(),
            "type": str(order.get_order_type()),
            "timestamp": timestamp,
            "newOrderRespType": "RESULT",
        }

        signature = compute_signature(payload, self._binance_key_secret)
        payload['signature'] = signature
        
        return {
            "id": message_id,
            "method": "order.place",
            "params": payload
        }
                        
    async def on_open(self):
        log.info('WS connection opened ..')
        await self.init_lot_sizes()
        input()
        while True:
            log.info(f'Reinitializing portfolio, getting coin balances')
            await self.get_balances()
            log.info('Listening to signals queue ..')
            signal = self.q.get()
            log.info('Caught new signal ..')
            if signal is None:
                break
            await self.process_signal(signal)
            
    async def run_(self, q :multiprocessing.Queue):
        self.q = q
        log.info('Order handler running ..')
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(self._websocket_endpoint) as ws:
                self.ws = ws
                await self.on_open()

    def run(self, q :multiprocessing.Queue):
        asyncio.run(self.run_(q))
        

def main():
    log.info("Order Handler starting main process")

    config = configparser.ConfigParser()
    config.read('config.ini')

    q = multiprocessing.Queue()
    oh = OrderHandler(config)
    ohp = multiprocessing.Process(name='OrderHandler', target=oh.run, args=(q,))
    ohp.start()
    # path = [

    #     Order(CoinPair("ETH", "BTC"), Way.SELL),
    #     Order(CoinPair("BNB", "BTC"), Way.BUY),
    #     Order(CoinPair("BNB", "ETH"), Way.SELL),
    # ]
    # signal = Signal(
    #     path,
    #     "TESTING SIGNAL",
    #     1
    # )

    path=[Order(CoinPair("REEF", "USDT"), Way.SELL, type=OrderType.MARKET, quantity=0.01)]
    signal = Signal(
        path,
        "SELL REEF",
        1
    )

    log.info("Sleeping 3s before launching signal")
    time.sleep(3)
    q.put(signal)
    log.info("Signal launched")
    ohp.join()


if __name__ == '__main__':
    main()
