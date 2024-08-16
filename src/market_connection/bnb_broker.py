import signal
import asyncio 
import aiohttp
import json
import uuid
from src.common.financial_objects import Order, Way, CoinPair, OrderType
from src.common.utils import get_timestamp, signal_handler, init_logger, compute_signature

signal.signal(signal.SIGINT, signal_handler)
log = init_logger('BNBBroker')
STATUS_OK=200
        
class BNBCommands:
    def __init__(self, config):
        market_connection = config['BROKER']['market_connection']
        self._binance_api_key = config[market_connection]['api_key']
        self._binance_key_secret = config[market_connection]['key_secret']

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

class BNBWSClient:
    def __init__(self, config):
        market_connection = config['BROKER']['market_connection']        
        self._websocket_endpoint = config[market_connection]['websocket_endpoint']

    def __del__(self):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.session.close())
            else:
                loop.run_until_complete(self.session.close())
        except Exception:
            pass
                
    async def establish_connection(self):
        self.session = aiohttp.ClientSession()
        self.ws = await self.session.ws_connect(self._websocket_endpoint, max_msg_size = 10 * 1024 * 1024)
        log.info(f'Binance client WS connection established')

    async def execute_command(self, command, *args):
        message_id = await self.send_command(command, *args)
        log.warning(f'Waiting for response for {message_id}')
        raw_response = await self.listen_socket()
        message_json = json.loads(raw_response)
        rmessage_id = message_json.get('id')
        message_result = message_json.get('result')
        if rmessage_id is None or rmessage_id != message_id:
            raise Exception(f"[BNB] Recieved message id [{rmessage_id}] different than awaited [{message_id}]")
        if message_json.get('status') != STATUS_OK:
            raise Exception(f"[BNB] Market reject, reason [{message_json.get('error')}]")
        log.warning(f'Received response for {message_id}')
        return message_result 

    async def listen_socket(self):
        wsMessage = await self.ws.receive()
        # log.debug(f'Got message on ws: {wsMessage}')
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

class BNBBroker:
    def __init__(self, config):
        market_connection = config['BROKER']['market_connection']        
        self._websocket_endpoint = config[market_connection]['websocket_endpoint']
        self.commands = BNBCommands(config)
        self.ws_client = BNBWSClient(config)
        
    async def init(self):
        await self.ws_client.establish_connection() 
            
    async def get_balances(self): #dict(str, float)
        account_status = await self.ws_client.execute_command(self.commands.get_account_status_command)
        balance = {}
        for asset_balance_obj in account_status['balances']:
            balance[str(asset_balance_obj['asset'])]=float(asset_balance_obj['free'])
        return balance
    
    async def execute_order(self, order:Order):
        if order.get_type() != OrderType.MARKET:
            log.error(f'Unhandled order type : {order.get_type()}')
        log.info(f'Sending market order way=[{order.get_way()}] symbol=[{order.get_symbol()}] qty=[{order.get_quantity()}]')
        exec_response = await self.ws_client.execute_command(self.commands.place_order_command, order)
        return exec_response
    
    async def get_symbols(self):
        log.info('Getting exchange info')
        exchange_info = await self.ws_client.execute_command(self.commands.get_exchange_info_command)
        symbols = [] 
        for json_symbol in exchange_info['symbols']:
            if json_symbol['status']=='TRADING':
                symbol = CoinPair(
                            json_symbol['baseAsset'], 
                            json_symbol['quoteAsset'], 
                            json_symbol['symbol']
                        )
                for json_filter in json_symbol['filters']:
                    if json_filter['filterType'] == 'LOT_SIZE':
                        symbol.set_lot_size(float(json_filter['stepSize'])) 
                        symbol.set_min_size(float(json_filter['minQty']))
                        symbol.set_max_size(float(json_filter['maxQty']))     
                    if json_filter['filterType'] == 'MARKET_LOT_SIZE':
                        symbol.set_lot_size(float(json_filter['stepSize'])) 
                        symbol.set_min_size(float(json_filter['minQty']))
                        symbol.set_max_size(float(json_filter['maxQty']))     
                            
                symbols.append(symbol) 
        # symbols = [
        return symbols
