import signal
from strategy import ArbitrageStrategy
from bnb_broker import BNBBroker
from feed_handler import FeedHandler
from utils import AsyncMixin
import multiprocessing
from financial_objects import Signal
from utils import signal_handler, init_logger, TelegramSender

signal.signal(signal.SIGINT, signal_handler)
log = init_logger('StrategyRunner')


class StrategyRunner(AsyncMixin):
    async def __ainit__(self, config):

        self.strat = ArbitrageStrategy(config)
        self.broker = BNBBroker(config)
        self.telegram_sender = TelegramSender(config)
        
        await self.broker.init()

        symbols_list = await self.broker.get_symbols()         
        self.strat.init_strategy(symbols_list)

        balances = await self.broker.get_balances()
        self.strat.reset_balance(balances)

        symbols_list = self.strat.get_strat_symbols()
        
        self.q = multiprocessing.Queue()
        self.feeder = FeedHandler(config, symbols_list)
        self.feeder = multiprocessing.Process(name='FeedHandler', target=self.feeder.run, args=(self.q,))

    async def process_signal(self, signal: Signal):
        try:
            orders_list = signal.get_orders_list()
            log.info(f"Signal received:")
            log.info(f"Theo pnl = [{signal.get_theo_pnl()}]")
            log.info(f"Description = [{signal.get_description()}]")
            await self.telegram_sender.send_message(f"Signal received: \n\n Theo pnl = [{signal.get_theo_pnl()}] \n\n Description = [{signal.get_description()}]")
            for order in orders_list:
                
                exec_response = await self.broker.execute_order(order)
                log.info(f"exec : {exec_response}")
                log.info(f'Finished executing order')
        except Exception as e:
            log.critical('An exception occured during signal processing')
            log.exception(e)  
        
        
    async def run(self):
        self.feeder.start()
        try:
            await self.telegram_sender.send_message(f"Running Strategy, started feeder and broker, waiting for signals")
            while True:
                data = self.q.get()
                signal = self.strat.check_opportunity(data)
            
                if signal is None:
                    continue

                log.info('Caught new signal ..')
                await self.process_signal(signal)
                
                log.info(f'Reinitializing portfolio, getting coin balances')
                balances = await self.broker.get_balances()
                self.strat.reset_balance(balances)

        except Exception as e:
            log.critical('An exception occured during strategy run')
            log.exception(e)  

        self.feeder.terminate()
        self.feeder.join()
        return 
