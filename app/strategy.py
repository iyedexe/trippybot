from typing import List, Dict
from financial_objects import Way, Signal, OrderType, Order
from utils import init_logger
FEE = 0.1
RISK = 0.7
log = init_logger('Strategy')

# bid price is for price for selling base currency
# 1 quote == bid base
# BNB/USDT
#Sell BNB/USDT means:
    # give BNB -> get USDT
    # 1 BNB -> bid USDT 

#Buy BNB/USDT means:
    # give USDT -> get BNB
    # 1 USDT -> 1/ask BNB 

class ArbitrageStrategy:
    def __init__(self, path: List[Order], config):
        self.path = path
        self._config = config
        self.balance = None
        self.first_time=True
    
    def reset_balance(self, val):
        self.balance = val
    
    def check_opportunity(self, data: Dict):
        if self.balance is None:
            return None
        initial_order = self.path[0]
        
        available_amount = RISK * self.balance[initial_order.get_symbol()]
        cost = 1
        signal_desc = []
        
        for order in self.path:
            symbol_prices = data.get(order.get_symbol()) 
            if symbol_prices is None:
                log.warning(f'Market data on symbol {[order.get_symbol()]} unavailable, no signal')
                return None
                        
            order.set_quantity(available_amount)
            order.set_type(OrderType.MARKET)

            if order.get_way() == Way.SELL:
                bid = float(symbol_prices.get("b"))
                order.set_price(bid)
                cost *= bid
                available_amount *= bid
                
            elif order.get_way() == Way.BUY:
                ask = float(symbol_prices.get("a"))
                order.set_price(ask)
                cost *= (1/ask)
                available_amount *= (1/ask)
    
            order_desc = f'symbol=[{order.get_symbol()}], way=[{order.get_way()}] price=[{order.get_price()}], quantity=[{order.get_quantity()}]' 
            signal_desc.append(order_desc)
                            
        if self.first_time:
            self.first_time=False
            log.warning(f'Market data available, first frame: {data}')

        fees = pow(1 - FEE/100, 3)
        cost *= fees
        
        if cost<1:
            return None
            
        signal = Signal(
            orders = self.path,
            signal_description = f"Arbitrage opportunity : {' && '.join(signal_desc)}",
            theo_pnl = 100*cost
        )
        return signal
