from dataclasses import dataclass

from src.strategies.reinforcement_learning import ReinforcementLearningStrat
from src.strategies.supertrend import SuperTrendStrat
from src.strategies.triangular_arbitrage import TriangularArbitrage
from src.market_connection.bnb_feeder import TickBNBFeeder, CandleStickBNBFeeder
from src.strategies.istrategy import IStrategy
from src.market_connection.bnb_feeder import IBNBFeeder

@dataclass
class StrategyEnv:
    strat: IStrategy
    feed: IBNBFeeder

STRAT_MAP = {
    "reinforcement_learning" : StrategyEnv(ReinforcementLearningStrat, TickBNBFeeder),
    "supertrend" : StrategyEnv(SuperTrendStrat, CandleStickBNBFeeder), 
    "triangular_arbitrage" : StrategyEnv(TriangularArbitrage, TickBNBFeeder)
}

class StratFactory:
    @staticmethod
    def get_strategy(strategy_name: str, config):
        env = STRAT_MAP.get(strategy_name)
        if not env:
            return None
        return env.strat(config)

    @staticmethod
    def get_feeder(strategy_name: str, config):
        env = STRAT_MAP.get(strategy_name)
        if not env:
            return None
        return env.feed(config)
