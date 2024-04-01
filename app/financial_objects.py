from enum import Enum

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

    def get_symbol(self):
        return self.symbol

    def get_quote(self):
        return self._quote_asset

    def get_base(self):
        return self._base_asset
            
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
