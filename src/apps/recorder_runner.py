import signal
import os
import aiofiles
from src.market_connection.bnb_broker import BNBBroker
from src.market_connection.feed_handler import FeedHandler
from src.common import AsyncMixin
import multiprocessing
from src.common.financial_objects import MarketDataFrame
from src.common.utils import signal_handler, init_logger, get_data_path

signal.signal(signal.SIGINT, signal_handler)
log = init_logger('StrategyRunner')


class RecorderRunner(AsyncMixin):
    async def __ainit__(self, config):

        self.broker = BNBBroker(config)      
        await self.broker.init()

        self.symbols_list = await self.broker.get_symbols()         
       
        self.q = multiprocessing.Queue()
        self.fh = FeedHandler(config, self.symbols_list)
        self.fh_process = multiprocessing.Process(name='FeedHandler', target=self.fh.run, args=(self.q,))

    async def record_data(self, data: MarketDataFrame, format="csv"):
        try:
            symbol = data.get_symbol()
            date_str = data.get_date().strftime("%Y%m%d")
            file_folder = os.path.join(get_data_path(), "book", symbol, date_str)
            if not os.path.exists(file_folder):
                os.makedirs(file_folder)
            file_path = os.path.join(file_folder, f"data.{format}")
            if os.path.is_file(file_path):
                open_mode = "a"
                add_header = False
            else:
                open_mode = "w"
                add_header = True
            async with aiofiles.open(file_path, mode=open_mode) as f:
                if add_header:
                    await f.write(data.get_header_str())
                await f.write(data.get_frame_str())
        except Exception as e:
            log.critical('An exception occured during signal processing')
            log.exception(e)  
        
        
    async def run(self):
        log.info(f"Starting recorder runner on [{len(self.symbols_list)}] symbols")
        self.fh_process.start()
        try:
            while True:
                data = self.q.get()
                await self.record_data(data)
        except Exception as e:
            log.critical('An exception occured during strategy run')
            log.exception(e)  

        self.fh_process.terminate()
        self.fh_process.join()
        return 
