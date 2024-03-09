import requests
import multiprocessing
from fluxer import Fluxer
from path_finder import PathFinder
from strat import ArbitrageStrategy


if __name__ == '__main__':
    dico = PathFinder()
    arbitrage_paths = dico.init()
    print(arbitrage_paths)
    
    # path = arbitrage_paths[0]
    # strat = ArbitrageStrategy(path)

    # ticker_list = ["ETHBTC", "BNBBTC", "BNBETH"]
    # fluxer = Fluxer(ticker_list)
    # q = multiprocessing.Queue()    
    # fluxer = multiprocessing.Process(name='fluxer', target=fluxer.run, args=(q,))
    # # hitter = multiprocessing.Process(name='hitter', target=order_sender, args=(q,))
    # fluxer.start()
    # # hitter.start()
