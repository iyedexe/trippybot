import asyncio
import configparser
import argparse
import signal
from src.apps.strategy_runner import StrategyRunner
from src.common.utils import signal_handler

signal.signal(signal.SIGINT, signal_handler)

async def main():
    parser = argparse.ArgumentParser(description='This is a program that runs a trading strategy')
    parser.add_argument("-c", "--configfile", help="Name of the configuration file to use", dest="configfile")
    parser.add_argument("-s", "--strategy", help="Name of the strategy to be looked up in strategies folder", dest="strategy")
    args = parser.parse_args()                

    config = configparser.ConfigParser()
    config.read(args.configfile)
    runner = StrategyRunner(config, config.strategy)
    await runner.initialize()
    await runner.run()

if __name__ == "__main__":

    asyncio.run(main())

