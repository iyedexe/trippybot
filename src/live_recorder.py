import asyncio
import configparser
import signal
from apps.recorder_runner import RecorderRunner
from common.utils import signal_handler

signal.signal(signal.SIGINT, signal_handler)

async def main():
    config = configparser.ConfigParser()
    config.read('config.ini')
    runner = await RecorderRunner(config)
    await runner.run()

if __name__ == "__main__":
    asyncio.run(main())