import logging
import configparser
import multiprocessing

from src.market_connection.bnb_feeder import CandleStickBNBFeeder

def main():
    config = configparser.ConfigParser()
    config.read('config.ini')

    logging.root.setLevel(logging.DEBUG)
    fh = CandleStickBNBFeeder(config, ["BTCUSDT", "TRXUSDT"])
    q = multiprocessing.Queue()
    fh.run(q)

if __name__ == "__main__":
    main()