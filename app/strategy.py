from financial_objects import Way, Signal, OrderType
from multiprocessing.managers import BaseManager

FEE = 0.1
class StrategyManager(BaseManager):
    pass

class ArbitrageStrategy:
    def __init__(self, path, config):
        self.path = path
        self._config = config
        self.balance = None
    
    def reset_balance(self, val):
        self.balance = val
    
    def check_opportunity(self, data):
        # if self.balance is None:
        #     return None
        
        cost = 1
        for step in self.path:
            if data.get(step.get_ticker()) is None:
                return False
            if step._way == Way.SELL:
                cost *= float(data.get(step.get_ticker()).get("b"))
            elif step._way == Way.BUY:
                cost *= (1/float(data.get(step.get_ticker()).get("a")))
        fees = pow(1 - FEE/100, 3)
        cost *= fees
        
        if cost>=1:
            path_serial = [f'{step._way} {step.get_ticker()}@{data.get(step.get_ticker()).get("b" if step._way==Way.SELL else "a")}' for step in signal.get_orders()]
            for order in self.path:
                order.set_type(OrderType.MARKET)
                # order.set_size(MARKET)
                
            signal = Signal(
                orders = self.path,
                signal_description = f"Arbitrage opportunity : {' && '.join(path_serial)}",
                theo_pnl = cost
            )
            signal = self.path
            return signal
        return None
