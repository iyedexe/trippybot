from fin import Way
import telegram
import asyncio


FEE = 0.1

class ArbitrageStrategy:
    def __init__(self, path, config):
        self.path = path
        self._config = config 
        self._telegram_api_key = config['TELEGRAM']['api_key']
        self._telegram_user_id = config['TELEGRAM']['user_id']
        self._bot = None

    def send_message(self, message):
        asyncio.run(self._bot.send_message(chat_id=self._telegram_user_id, text=message))      
    
    def check_opportunity(self, data):
        if self._bot is None:
            self._bot = telegram.Bot(token=self._telegram_api_key)
        cost = 1
        # print(f"strategy data : {data}")
        for step in self.path:
            if data.get(step.get_ticker()) is None:
                return False
            if step._way == Way.SELL:
                cost *= float(data.get(step.get_ticker()).get("b"))
            elif step._way == Way.BUY:
                cost *= (1/float(data.get(step.get_ticker()).get("a")))
        fees = pow(1 - FEE/100, 3)
        cost *= fees
        print(f"theo unitairy pnl = {cost}")

        if cost>=1:
            print(f"arbitrage opportunity, theo unitairy pnl = {cost}")
            self.send_message(f"arbitrage opportunity, theo unitairy pnl = {cost}")
