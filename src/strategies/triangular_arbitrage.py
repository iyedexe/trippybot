from src.common.financial_objects import Way, Signal, OrderType, Order,CoinPair, MarketDataFrame
import datetime
import time
from timeit import default_timer as timer
from src.common.utils import init_logger
FEE = 0.1
RISK = 1
log = init_logger('Strategy')

class TriangularArbitrage:
    def __init__(self, config):
        self._config = config
        self._starting_coin = config['STRATEGY']['starting_coin']
        self.logging_interval = int(config['STRATEGY'].get('logging_interval', 60))
        self.balance = None
        self.data={}
        self.best_signal=None
        self.best_time=None
        self.best_pnl=None
        self.num_signals=0
        self.avg_signal_time=0
        self.prev_time = time.time()

    def get_steps(self, coin, pairs_universe: list[CoinPair]) -> list[Order]:
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
    
    def init_strategy(self, full_pairs_universe: list[CoinPair]):
        
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
        self.strat_symbols = list(set(self.strat_symbols))
        log.info(f'Found [{len(looping_paths)}] possible paths for arbitrage starting on [{self._starting_coin}]')
        log.info(f'Total used sybmols=[{len(self.strat_symbols)}], Total used assets=[{len(self.strat_assets)}]')
        return looping_paths
            
    def get_strat_symbols(self):
        return self.strat_symbols
        
    def reset_balance(self, val):
        self.balance = val
        for asset in self.strat_assets:
            log.info(f'Starting balance on [{asset}]=[{self.balance[asset]}]')
    
    def evaluate_path(self, path: list[Order]):
        signal_desc = []

        initial_order = path[0]
        
        initial_amount = RISK * self.balance[initial_order.get_initial()]
        order_pair = initial_order.get_pair()    
        initial_amount = order_pair.validate_quantity(initial_amount)
        available_amount = initial_amount
        
        if available_amount == 0:
            log.error(f"Cannot price strategy, available amount is null on [{initial_order.get_initial()}]")
            return None, ""

        for order in path:
            symbol_last_update = self.data.get(order.get_symbol()) 
            if symbol_last_update is None:
                log.debug(f'Market data on symbol {[order.get_symbol()]} unavailable, no signal')
                return None, ""
                        
            order.set_quantity(available_amount)
            order.set_type(OrderType.MARKET)

            if order.get_way() == Way.SELL:
                bid = symbol_last_update.get_bid()
                if bid == 0:
                    log.error(f'Error on market data for symbol {[order.get_symbol()]} bid=[{bid}]')
                    return None, ""                    
                order.set_price(bid)
                available_amount *= bid 
                
            elif order.get_way() == Way.BUY:
                ask = symbol_last_update.get_ask()
                if ask == 0:
                    log.error(f'Error on market data for symbol {[order.get_symbol()]} bid=[{ask}]')
                    return None, ""
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
    
    def log_stats_info(self):
        current_time = time.time()
        if current_time > self.prev_time + self.logging_interval:
            self.prev_time = current_time
            log.info(f"Strategy running on [{len(self.strat_paths)}]")
            log.info(f"Processes [{self.num_signals}] signals in total with and avg time of [{self.avg_signal_time}]")
            if self.best_pnl is None:
                log.info("No signal yet computed, market data unavailable")
                return
            log.info(f"Best signal so far occured @ [{datetime.datetime.fromtimestamp(self.best_time).strftime('%Y-%m-%dT%H:%M:%SZ')}]"
                     f"PNL=[{self.best_pnl}]"
                     f"DESC=[{self.best_signal.get_description()}]")
    
    def check_opportunity(self, data: MarketDataFrame):
        start = timer()
        impacted_paths=[]

        # Determine arbitrage paths impacted by MD update
        update_symbol = data.get_symbol()
        self.data[update_symbol] = data
        for path in self.strat_paths:
            for step in path:
                if (self.data.get(step.get_symbol()) is not None) and (step.get_symbol() == update_symbol):
                    impacted_paths.append(path)
                    break
                                
        # Compute PNL for every path and generate signal for most profitable
        signal = None
        max_pnl = 0
        for path in impacted_paths:
            
            pnl ,signal_desc = self.evaluate_path(path)
            if pnl is None:
                continue
                                     
            if pnl>max_pnl:
                max_pnl = pnl                                
                signal = Signal(
                    orders = path,
                    signal_description = signal_desc,
                    theo_pnl = pnl
                )

            if self.best_pnl is None or pnl>self.best_pnl:
                self.best_signal = Signal(
                    orders = path,
                    signal_description = signal_desc,
                    theo_pnl = pnl
                )
                self.best_pnl = pnl
                self.best_time = time.time()
                    
        end = timer()
        elapsed_time = end - start
        self.num_signals +=1
        self.avg_signal_time += elapsed_time/self.num_signals
        self.log_stats_info()

        return signal
        