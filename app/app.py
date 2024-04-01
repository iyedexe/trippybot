import asyncio
import configparser
import signal
from strategy_runner import StrategyRunner
from utils import signal_handler, init_logger

# log = init_logger("MainApp")

signal.signal(signal.SIGINT, signal_handler)

async def main():
    config = configparser.ConfigParser()
    config.read('config.ini')
    runner = await StrategyRunner(config)
    await runner.run()

if __name__ == "__main__":

    asyncio.run(main())