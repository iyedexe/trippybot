import asyncio
import configparser
import signal
from src.apps.strategy_runner import StrategyRunner
from src.common.utils import signal_handler

signal.signal(signal.SIGINT, signal_handler)

async def main():
    config = configparser.ConfigParser()
    config.read('config.ini')
    runner = await StrategyRunner(config)
    await runner.run()

if __name__ == "__main__":

    asyncio.run(main())