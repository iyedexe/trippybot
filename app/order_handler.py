# import telegram
import signal
from collections import defaultdict 
from financial_objects import Order, Signal, Way, CoinPair, OrderType
from utils import get_timestamp, signal_handler, init_logger, compute_signature, TelegramSender
from strategy import ArbitrageStrategy
from bnb_broker import BNBBroker

signal.signal(signal.SIGINT, signal_handler)
# log = init_logger('OrderHandler')
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
