from enum import Enum
from utils import init_logger

log = init_logger("FinObjects")

class Way(Enum):
    BUY  = 0
    SELL = 1
    HOLD = 2

    def __str__(self):
        return self.name

class OrderType(Enum):
    MARKET = 0
    LIMIT = 1

    def __str__(self):
        return self.name
    
class CoinPair:
    def __init__(self, base, quote, symbol=None):
        self._base_asset = base
        self._quote_asset = quote
        if symbol is None:
            self.symbol = f"{self._base_asset}{self._quote_asset}"
        else:
            self.symbol = symbol
        self.min_size = None
        self.lot_size = None
        self.max_size = None

    def get_symbol(self):
        return self.symbol

    def get_quote(self):
        return self._quote_asset

    def get_base(self):
        return self._base_asset

    def get_lot_size(self):
        return self.lot_size
    
    def set_lot_size(self, value :float): 
        if (self.lot_size is None) or (value>self.lot_size):
            self.lot_size = value
    
    def get_min_size(self):
        return self.min_size
            
    def set_min_size(self, value :float): 
        if (self.min_size is None) or (value>self.min_size):
            self.min_size = value

    def get_max_size(self):
        return self.max_size
    
    def set_max_size(self, value :float): 
        if (self.max_size is None) or (value<self.lot_size):
            self.max_size = value
            
    def validate_quantity(self, quantity):
        new_quantity = quantity
        if self.lot_size !=0 and (quantity % self.lot_size) != 0:
            new_quantity = quantity - (quantity % self.lot_size)
            log.debug(f"Corrected size on {self.symbol} using lot_size {self.lot_size} : [{quantity}]->[{new_quantity}]")
        # if self.min_size !=0 and quantity < self.min_size:
        #     quantity = self.min_size
        # if self.max_size !=0 and quantity > self.max_size:
        #     quantity = self.max_size
        return new_quantity
            
    def __str__(self):
        return f"{self._base_asset}/{self._quote_asset}"

    def __repr__(self):
        return f"{self._base_asset}/{self._quote_asset}"

    def __eq__(self, other):
        return self._base_asset == other._base_asset and self._quote_asset == other._quote_asset
    

class Order:
    def __init__(self, pair: CoinPair, way:Way, type:OrderType=None, quantity=None, price=None):
        self._pair = pair
        self._way = way
        self._type =type
        self._quantity = quantity
        self._price = price

    def __str__(self):
        return f"{self._way}@{self._pair}"

    def __repr__(self):
        return f"{self._way}@{self._pair}"
    
    def get_way_key(self):
        if self._way == Way.BUY:
            return "a" 
        if self._way == Way.SELL:
            return "b" 
    
    def get_symbol(self):
        return self._pair.get_symbol()
    
    def get_way(self):
        return self._way

    def get_quantity(self):
        return self._quantity
    def set_quantity(self, value):
        self._quantity = value

    def get_pair(self):
        return self._pair

    def get_target(self):
        if self._way == Way.SELL:
            return self._pair.get_quote()
        elif self._way == Way.BUY:
            return self._pair.get_base()
        else:
            return None

    def get_initial(self):
        if self._way == Way.SELL:
            return self._pair.get_base()
        elif self._way == Way.BUY:
            return self._pair.get_quote()
        else:
            return None
        
    def get_type(self):
        return self._type
    def set_type(self, value):
        self._type = value

    def get_price(self):
        return self._price
    def set_price(self, value):
        self._price = value
        
class Signal:
    def __init__(self, orders , signal_description ,theo_pnl : float):
        self.orders = orders
        self.signal_description = signal_description
        self.theo_pnl = theo_pnl
        
    def get_orders_list(self):
        return self.orders

    def get_theo_pnl(self):
        return self.theo_pnl
    
    def get_description(self):
        return self.signal_description
    
class MarketDataFrame:
    def __init__(self, symbol, bid, bid_qty, ask, ask_qty):
        self.symbol = symbol
        self.ask = float(ask)
        self.bid = float(bid)
        self.ask_qty = float(ask_qty)
        self.bid_qty = float(bid_qty)

    def get_symbol(self):
        return self.symbol
    def get_bid(self):
        return self.bid
    def get_ask(self):
        return self.ask
    
    def __str__(self):
        return f"s=[{self.symbol}];b=[{self.bid_qty}]@[{self.bid}];a=[{self.ask_qty}]@[{self.ask}]"