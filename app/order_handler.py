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
from utils import get_timestamp, signal_handler, init_logger, compute_signature, TelegramSender
from strategy import ArbitrageStrategy

signal.signal(signal.SIGINT, signal_handler)
log = init_logger('OrderHandler')
STATUS_OK=200

class OrderController:
    def __init__(self):
        self.lot_size = defaultdict(float) 
        self.min_size = defaultdict(float)
        self.max_size = defaultdict(float)
        
    def init(self, exchange_info):
        log.info('Initializing lot sizes')
        for symbol_obj in exchange_info['symbols']:
            symbol = symbol_obj['symbol']
            for filter_obj in symbol_obj['filters']:
                if filter_obj['filterType'] == 'LOT_SIZE':
                    self.lot_size[symbol] = float(filter_obj['stepSize']) 
                    self.min_size[symbol] = float(filter_obj['minQty'])
                    self.max_size[symbol] = float(filter_obj['maxQty'])

    def control_size(self, order :Order):
        symbol = order.get_symbol()
        qty = order.get_quantity()
                
        if self.lot_size[symbol] !=0 and (qty % self.lot_size[symbol]) != 0:
            qty = int(qty/self.lot_size[symbol]) * self.lot_size[symbol]
        if self.min_size[symbol] !=0 and qty < self.min_size[symbol]:
            qty = self.min_size[symbol]
        if self.max_size[symbol] !=0 and qty > self.max_size[symbol]:
            qty = self.max_size[symbol]
            
        order.set_quantity(qty)
        
class OrderHandler:
    def __init__(self, config, strat : ArbitrageStrategy):
        self._config = config
        market_connection = config['ORDER_HANDLER']['market_connection']

        self._websocket_endpoint = config[market_connection]['websocket_endpoint']
        self._binance_api_key = config[market_connection]['api_key']
        self._binance_key_secret = config[market_connection]['key_secret']
        self.balance = defaultdict(float)
        self.dry_run = config['ORDER_HANDLER'].getboolean('dry_run', True)
        self.order_controller = OrderController()
        self.telegram_sender = TelegramSender(config)
        self.strat = strat

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
        log.warning(f'Send command {command.__name__} with {message_id}')
        await self.ws.send_str(message_to_server)
        return message_id
    
    async def wait_response(self, message_id):
        log.warning(f'Waiting for response for {message_id}')
        raw_response = await self.listen_socket()
        # log.debug(f'raw response : {raw_response}')    
        message_json = json.loads(raw_response)
        rmessage_id = message_json.get('id')
        message_result = message_json.get('result')
        if rmessage_id is None or rmessage_id != message_id:
            raise Exception(f"[BNB] Recieved message id [{rmessage_id}] different than awaited [{message_id}]")
        if message_json.get('status') != STATUS_OK:
            raise Exception(f"[BNB] Market reject, reason [{message_json.get('error')}]")
        log.warning(f'Received response for {message_id}')
        return message_result 

    async def process_signal(self, signal: Signal):
        try:
            orders_list = signal.get_orders_list()
            log.info(f"Signal received:")
            log.info(f"Theo unitairy pnl = [{signal.get_theo_pnl()}%]")
            log.info(f"Description = [{signal.get_description()}]")
            self.telegram_sender.send_message(f"Signal received: \n\n Theo unitairy pnl = [{signal.get_theo_pnl()}%] \n\n Description = [{signal.get_description()}]")
            for order in orders_list:
                
                self.order_controller.control_size(order)
                await self.execute_order(order)

                log.info(f'Finished executing order')
        except Exception as e:
            log.critical('An exception occured during signal processing')
            log.exception(e)  

    async def get_balances(self):
        message_id = await self.send_command(self.get_account_status_command)
        account_status = await self.wait_response(message_id)
        
        
        for asset_balance_obj in account_status.get('balances'):
            self.balance[str(asset_balance_obj['asset'])]=float(asset_balance_obj['free'])
            if str(asset_balance_obj['asset']) in ['BNB', 'USDT']:
                log.debug(f'Current balance of [{asset_balance_obj["asset"]}] == [{asset_balance_obj["free"]}]')
    
    async def execute_order(self, order:Order):
        if order.get_type() != OrderType.MARKET:
            log.error(f'Unhandled order type : {order.get_type()}')
        log.info(f'Sending market order way=[{order.get_way()}] symbol=[{order.get_symbol()}] qty=[{order.get_quantity()}]')
        if self.dry_run == True:
            return
        message_id = await self.send_command(self.place_order_command, order)
        exec_response = await self.wait_response(message_id)

        log.info(f'ack_response : {exec_response}')
        log.info('Finished')
    
    async def init_lot_sizes(self):
        log.info('Getting exchange info')
        message_id = await self.send_command(self.get_exchange_info_command)
        exchange_info = await self.wait_response(message_id)
        self.order_controller.init(exchange_info)
        
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
        #see implementation choice #1
        if order.get_way() == Way.SELL:
            quantity_key = "quantity"
        elif order.get_way() == Way.BUY:
            quantity_key = "quoteOrderQty"

        payload = {
            "apiKey": self._binance_api_key,
            quantity_key: f"{order.get_quantity():.8f}",
            "side": str(order.get_way()),
            "symbol": order.get_symbol(),
            "type": str(order.get_type()),
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
        log.info(f'Initializing portfolio, getting coin balances')
        await self.get_balances()
        self.strat.reset_balance(self.balance)
        self.telegram_sender.send_message(f"Running Strategy, order handler started!")
        log.info(f'Init done, starting market data listen')

        while True:

            data = self.q.get()
            signal = self.strat.check_opportunity(data)
            # log.info(f'New market data incoming :[{data}]')
            
            if signal is None:
                continue

            log.info('Caught new signal ..')
            await self.process_signal(signal)
            log.info(f'Reinitializing portfolio, getting coin balances')
            await self.get_balances()
            self.strat.reset_balance(self.balance)

            
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
    s = ArbitrageStrategy()
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
    path=[Order(CoinPair("BNB", "USDT"), Way.SELL, type=OrderType.MARKET, quantity=0.01)]
    signal = Signal(
        path,
        "SELL BNB",
        1
    )

    log.info("Sleeping 3s before launching signal")
    time.sleep(3)
    q.put(signal)
    log.info("Signal launched")
    ohp.join()


if __name__ == '__main__':
    main()
