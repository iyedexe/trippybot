import configparser
import multiprocessing
from app.feed_handler import FeedHandler
from app.path_finder import PathFinder
from app.strategy import ArbitrageStrategy
from app.financial_objects import Order, Way, CoinPair
from app.order_handler import OrderHandler


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    # dico = PathFinder()
    # arbitrage_paths = dico.init()
    # print(arbitrage_paths)
    
    # path = arbitrage_paths[0]
    # strat = ArbitrageStrategy(path)

    # ticker_list = ["ETHBTC", "BNBBTC", "BNBETH"]
    # fluxer = Fluxer(ticker_list)
    # q = multiprocessing.Queue()    
    # fluxer = multiprocessing.Process(name='fluxer', target=fluxer.run, args=(q,))
    # # hitter = multiprocessing.Process(name='hitter', target=order_sender, args=(q,))
    # fluxer.start()
    # # hitter.start()

    ticker_list = ["ETHBTC", "BNBBTC", "BNBETH"]
    
    q = multiprocessing.Queue()
    path = [
        Order(CoinPair("ETH", "BTC"), Way.SELL),
        Order(CoinPair("BNB", "BTC"), Way.BUY),
        Order(CoinPair("BNB", "ETH"), Way.SELL),
    ]
    strat = ArbitrageStrategy(path, config)
    fh = FeedHandler(ticker_list, strat)
    fhp = multiprocessing.Process(name='FeedHandler', target=fh.run, args=(q,))
    fhp.start()
    
    oh = OrderHandler(ticker_list, strat)
    ohp = multiprocessing.Process(name='OrderHandler', target=oh.run, args=(q,))
    ohp.start()