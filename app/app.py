import configparser
import signal
import multiprocessing
from feed_handler import FeedHandler
# from path_finder import PathFinder
from strategy import ArbitrageStrategy, StrategyManager
from financial_objects import Order, Way, CoinPair
from order_handler import OrderHandler
from utils import signal_handler, init_logger

signal.signal(signal.SIGINT, signal_handler)
# log = init_logger('ArbitrageStrat')

def main():
    config = configparser.ConfigParser()
    config.read('config.ini')

    q = multiprocessing.Queue()
    path = [
        Order(CoinPair("ETH", "BTC"), Way.SELL),
        Order(CoinPair("BNB", "BTC"), Way.BUY),
        Order(CoinPair("BNB", "ETH"), Way.SELL),
    ]
    strat = ArbitrageStrategy(path, config)

    fh = FeedHandler(config, ["ETHBTC", "BNBBTC", "BNBETH"])
    fhp = multiprocessing.Process(name='FeedHandler', target=fh.run, args=(q,strat))
    fhp.start()
    
    oh = OrderHandler(config)
    ohp = multiprocessing.Process(name='OrderHandler', target=oh.run, args=(q,strat))
    ohp.start()
    return 

    StrategyManager.register('ArbitrageStrategy', ArbitrageStrategy)
    with StrategyManager() as manager:
        
        # dico = PathFinder()
        # arbitrage_paths = dico.init()
        # print(arbitrage_paths)
        
        # path = arbitrage_paths[0]
        # strat = ArbitrageStrategy(path)

        q = multiprocessing.Queue()
        path = [
            Order(CoinPair("ETH", "BTC"), Way.SELL),
            Order(CoinPair("BNB", "BTC"), Way.BUY),
            Order(CoinPair("BNB", "ETH"), Way.SELL),
        ]
        strat = manager.ArbitrageStrategy(path, config)
        
        ticker_list = ["ETHBTC", "BNBBTC", "BNBETH"]        

        fh = FeedHandler(config, ticker_list)
        fhp = multiprocessing.Process(name='FeedHandler', target=fh.run, args=(q,strat))
        fhp.start()
        
        oh = OrderHandler(config)
        ohp = multiprocessing.Process(name='OrderHandler', target=oh.run, args=(q,strat))
        ohp.start()

if __name__ == '__main__':
    main()
