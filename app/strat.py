from fin import Way


FEE = 0.1

class ArbitrageStrategy:
    def __init__(self, path):
        self.path = path
    
    def check_opportunity(self, data):
        cost = 1
        # print(f"strategy data : {data}")
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
            print(f"arbitrage opportunity, theo unitairy pnl = {cost}")
