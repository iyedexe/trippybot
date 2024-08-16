from dataclasses import dataclass

from src.strategies.reinforcement_learning import ReinforcementLearningStrat
from src.strategies.supertrend import SuperTrendStrat
from src.strategies.triangular_arbitrage import TriangularArbitrage
from src.market_connection.feed_handler import TickFeedHandler, CandleStickFeedHandler
from src.strategies.istrategy import IStrategy
from src.market_connection.feed_handler import IFeeder

@dataclass
class StrategyEnv:
    strat: IStrategy
    feed: IFeeder

STRAT_MAP = {
    "reinforcement_learning" : StrategyEnv(ReinforcementLearningStrat, TickFeedHandler),
    "supertrend" : StrategyEnv(SuperTrendStrat, CandleStickFeedHandler), 
    "triangular_arbitrage" : StrategyEnv(TriangularArbitrage, TickFeedHandler)
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
