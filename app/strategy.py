from typing import List, Dict
from financial_objects import Way, Signal, OrderType, Order,CoinPair, MarketDataFrame
from collections import defaultdict
from utils import init_logger
FEE = 0.1
RISK = 1
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
    def __init__(self, config):
        self._config = config
        self._starting_coin = config['STRATEGY']['starting_coin']
        self.balance = None
        self.is_data_complete = defaultdict(bool)

    def get_steps(self, coin, pairs_universe) -> List[Order]:
        steps = []
        for pair in pairs_universe:
            if coin == pair.get_base():
                way = Way.SELL
            elif coin == pair.get_quote():
                way = Way.BUY
            else:
                continue
            steps.append(Order(pair, way))
        return steps
    
    def init_strategy(self, full_pairs_universe = List[CoinPair]):
        
        first_steps = self.get_steps(self._starting_coin, full_pairs_universe)
        prev_paths = [[step] for step in first_steps]
        arbitrage_depth =3

        for i in range(arbitrage_depth-1):
            paths=[]
            for path in prev_paths:
                f_order = path[-1]
                result_coin = f_order.get_target()  # gives quote if sell, base if buy
                used_coins = [order.get_pair() for order in path]
                remaining_coins = [x for x in full_pairs_universe if x not in used_coins]
                next_steps = self.get_steps(result_coin, remaining_coins)
                paths += [[*path, next_step] for next_step in next_steps]
            prev_paths=paths
        
        looping_paths = []
        for path in paths:
            last_order = path[-1]
            if last_order.get_target() == self._starting_coin:
                looping_paths.append(path)
                
        self.strat_paths = looping_paths
        
        log.info(f'Using paths : [{self.strat_paths}]')
        self.strat_symbols = []
        self.strat_assets = []
        for upath in self.strat_paths:
            self.strat_symbols += [order.get_symbol() for order in upath]
            self.strat_assets += [order.get_pair().get_base() for order in upath]
            self.strat_assets += [order.get_pair().get_quote() for order in upath]
            
        self.strat_assets = list(set(self.strat_assets))
        log.info(f'Found [{len(looping_paths)}] possible paths for arbitrage starting on [{self._starting_coin}]')
        return looping_paths
            
    def get_strat_symbols(self):
        return self.strat_symbols
        
    def reset_balance(self, val):
        self.balance = val
        for asset in self.strat_assets:
            log.info(f'Starting balance on [{asset}]=[{self.balance[asset]}]')
    
    def evaluate_path(self, path: List[Order], data: MarketDataFrame):
        signal_desc = []

        initial_order = path[0]
        
        initial_amount = RISK * self.balance[initial_order.get_initial()]
        order_pair = initial_order.get_pair()    
        initial_amount = order_pair.validate_quantity(initial_amount)
        available_amount = initial_amount
        
        if available_amount == 0:
            log.error(f"Cannot price strategy, available amount is null on [{initial_order.get_initial()}]")
            return 0, ""

        for order in path:
            symbol_prices = data.get(order.get_symbol()) 
            if symbol_prices is None:
                log.debug(f'Market data on symbol {[order.get_symbol()]} unavailable, no signal')
                return -1, ""
                        
            order.set_quantity(available_amount)
            order.set_type(OrderType.MARKET)

            if order.get_way() == Way.SELL:
                bid = float(symbol_prices.get("b"))
                if bid == 0:
                    log.error(f'Error on market data for symbol {[order.get_symbol()]} bid=[{bid}], raw=[{symbol_prices.get("b")}]')
                    return 0, ""                    
                order.set_price(bid)
                available_amount *= bid 
                
            elif order.get_way() == Way.BUY:
                ask = float(symbol_prices.get("a"))
                if ask == 0:
                    log.error(f'Error on market data for symbol {[order.get_symbol()]} bid=[{ask}], raw=[{symbol_prices.get("a")}]')
                    return 0, ""
                order.set_price(ask)
                available_amount *= (1/ask)
                
            available_amount = available_amount*(1 - FEE/100)
            order_pair = order.get_pair()
            available_amount = order_pair.validate_quantity(available_amount)
    
            order_desc = f'symbol=[{order.get_symbol()}], way=[{order.get_way()}] price=[{order.get_price()}], quantity=[{order.get_quantity()}]' 
            signal_desc.append(order_desc)
        
        pnl = available_amount - initial_amount
        signal_desc_str = f"Arbitrage opportunity : {' && '.join(signal_desc)}"
        log.debug(f"Signal pnl: {pnl} starting amount=[{initial_amount}], final amount=[{available_amount}] \ {signal_desc}")

        return pnl, signal_desc_str
        
    def check_opportunity(self, data: Dict):
        if self.balance is None:
            return None
        signal = None
        max_pnl = 0
        for i,path in enumerate(self.strat_paths):
            
            pnl ,signal_desc = self.evaluate_path(path, data)
            
            if pnl == -1:
                continue
            
            if not self.is_data_complete[i]:
                self.is_data_complete[i] = True
                log.info(f"Market data available for path {i}, data={data}")   
                         
            if pnl>max_pnl:
                max_pnl = pnl                                
                signal = Signal(
                    orders = path,
                    signal_description = signal_desc,
                    theo_pnl = pnl
                )
        return signal
