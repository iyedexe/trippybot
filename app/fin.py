from enum import Enum

class Way(Enum):
    BUY  = 0
    SELL = 1
    HOLD = 2

    def __str__(self):
        return self.name

class CoinPair:
    def __init__(self, base_symbol, quote_symbol):
        self._base_asset = base_symbol
        self._quote_asset = quote_symbol
    
    def __str__(self):
        return f"{self._base_asset}/{self._quote_asset}"

    def __repr__(self):
        return f"{self._base_asset}/{self._quote_asset}"

    def __eq__(self, other):
        return self._base_asset == other._base_asset and self._quote_asset == other._quote_asset
    
    def get_ticker(self):
        ticker =  f"{self._base_asset}{self._quote_asset}"
        return ticker.upper()


class Transaction:
    def __init__(self, pair: CoinPair, way:Way):
        self._pair = pair
        self._way = way

    def __str__(self):
        return f"{self._way}@{self._pair}"

    def __repr__(self):
        return f"{self._way}@{self._pair}"
    
    def get_way_key(self):
        if self._way == Way.BUY:
            return "a" 
        if self._way == Way.SELL:
            return "b" 

    def get_ticker(self):
        return self._pair.get_ticker()