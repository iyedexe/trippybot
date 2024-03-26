# import telegram
import signal
import asyncio 
import multiprocessing
import aiohttp
import json
import uuid
import configparser
import time
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

        self._conditions = {}
        self._message_response = {}
        self._bot = None
        # self.start_listen=asyncio.Event()

    async def send_command(self, command, *args):
        message_id = str(uuid.uuid4())
        self._conditions[message_id] = asyncio.Event()
        object_res = command(message_id, *args)
        log.warning(object_res)
        message_to_server = json.dumps(object_res)
        await self.ws.send_str(message_to_server)
        return message_id
    
    async def wait_response(self, message_id):
        log.warning(f'waiting for {message_id}')
        await self._conditions[message_id].wait()
        response = self._message_response.pop(message_id)
        del self._conditions[message_id]
        if response.get('status') != STATUS_OK:
            raise Exception(f"[BNB] Response NOK [{response.get('error')}]")
        return response.get('result')    

    async def process_signal(self, signal: Signal):
        orders_list = signal.get_orders_list()
        log.info(f"Signal received:\n"
              f"\tTheo unitairy pnl = [{signal.get_theo_pnl()}],\n" 
              f"\tDescription = [{signal.get_description()}]")

        for order in orders_list:

            pair = order.get_pair()
            if order.get_way() == Way.BUY:
                starting_coin = pair.get_quote_currency()
            elif order.get_way() == Way.SELL:
                starting_coin = pair.get_base_currency()

            balance = await self.get_balance(starting_coin)
            log.info(f'Current balance of {starting_coin} : {balance}')
            
            await self.execute_order(order)

            balance = await self.get_balance(starting_coin)
            log.info(f'Current balance of {starting_coin} : {balance}')

            log.info(f'Finshed executing order')

    async def get_balance(self, asset):
        log.info(f'Getting balance for {asset}')
        message_id = await self.send_command(self.get_account_status_command)
        await self.listen_socket()
        accountStatus = await self.wait_response(message_id)

        balance = 0
        for balanceJson in accountStatus.get('balances'):
            if balanceJson.get('asset') == asset:
                balance=float(balanceJson.get('free'))
        return balance
    
    async def execute_order(self, order:Order):
        if order.getType() != OrderType.MARKET:
            log.error(f'Unhandled order type : {order.getType()}')
        message_id = await self.send_command(self.place_order_command, order)
        await self.listen_socket()
        exec_response = await self.wait_response(message_id)
        log.info(f'ack_response : {exec_response}')
        log.info('Finished')
        
        # await self.listen_socket()
        # exec_response = await self.wait_response(message_id)
        # print(exec_response)
    
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

    async def listener_run_(self):
        await self.start_listen.wait()
        while True:
            await self.listen_socket()

    def listener_run(self):
        asyncio.run(self.listener_run_())
        
    async def listen_socket(self):
        wsMessage = await self.ws.receive()
        # log.critical(wsMessage)
        if wsMessage.type == aiohttp.WSMsgType.ERROR:
            self.on_error(wsMessage)

        if wsMessage.type == aiohttp.WSMsgType.TEXT:
            txtMessage = wsMessage.data
            self.on_message(txtMessage)
    
    async def on_open(self):
        log.info('WS connection opened ..')
        # listener = threading.Thread(target=self.listener_run)
        # listener.start()
        while True:
            log.info('Listening to signals queue ..')
            signal = self.q.get()
            log.info('Caught new signal ..')
            if signal is None:
                break
            await self.process_signal(signal)
            

    def on_message(self, message):
        message_json = json.loads(message)
        message_id = message_json.get('id')
        if message_id is None:
            log.error(f'Message received with no id : {message}')
            return
        self._message_response[message_id] = message_json
        self._conditions[message_id].set()


    def on_error(self, error):
        log.critical(f'Received error message : {error}')

    def on_close(self, close_status_code, close_msg):
        log.warning("Connection close")
        log.info(close_status_code)
        log.info(close_msg)

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

    path=[Order(CoinPair("BNB", "USDT"), Way.SELL, type=OrderType.MARKET, quantity=0.01)]
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
