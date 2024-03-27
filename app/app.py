import configparser
import signal
import multiprocessing
from feed_handler import FeedHandler
# from path_finder import PathFinder
from strategy import ArbitrageStrategy
from financial_objects import Order, Way, CoinPair
from order_handler import OrderHandler
from utils import signal_handler, init_logger

log = init_logger("MainApp")

signal.signal(signal.SIGINT, signal_handler)

def main():
    config = configparser.ConfigParser()
    config.read('config.ini')

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
    strat = ArbitrageStrategy(path, config)

    fh = FeedHandler(config, ["ETHBTC", "BNBBTC", "BNBETH"])
    fhp = multiprocessing.Process(name='FeedHandler', target=fh.run, args=(q,))
    fhp.start()
    try:
        oh = OrderHandler(config, strat)
        oh.run(q)
    except Exception as e:
        log.exception(e)    
    fhp.terminate()
    fhp.join()
    return 

if __name__ == '__main__':
    main()
