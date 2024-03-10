import configparser
import multiprocessing
from fluxer import Fluxer
from path_finder import PathFinder
from strat import ArbitrageStrategy
from fin import Transaction, Way, CoinPair


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
        Transaction(CoinPair("ETH", "BTC"), Way.SELL),
        Transaction(CoinPair("BNB", "BTC"), Way.BUY),
        Transaction(CoinPair("BNB", "ETH"), Way.SELL),
    ]
    strat = ArbitrageStrategy(path, config)
    fluxer = Fluxer(ticker_list, strat)
    fluxer = multiprocessing.Process(name='fluxer', target=fluxer.run, args=(q,))
    fluxer.start()