import os
import requests
import telegram
import logging
import hmac
import hashlib
import time
from urllib.parse import urlencode
from colorlog import ColoredFormatter
import sys

class AsyncMixin:
    def __init__(self, *args, **kwargs):
        """
        Standard constructor used for arguments pass
        Do not override. Use __ainit__ instead
        """
        self.__storedargs = args, kwargs
        self.async_initialized = False

    async def __ainit__(self, *args, **kwargs):
        """Async constructor, you should implement this"""

    async def __initobj(self):
        """Crutch used for __await__ after spawning"""
        assert not self.async_initialized
        self.async_initialized = True
        # pass the parameters to __ainit__ that passed to __init__
        await self.__ainit__(*self.__storedargs[0], **self.__storedargs[1])
        return self

    def __await__(self):
        return self.__initobj().__await__()



class TelegramSender:
    def __init__(self, config):
        self.config = config
        self._telegram_api_key = config['TELEGRAM']['api_key']
        self._telegram_user_id = config['TELEGRAM']['user_id']
        self._bot = None
        
    async def send_message(self, message):
        if self._bot is None:
            self._bot = telegram.Bot(token=self._telegram_api_key)
        
            await self._bot.send_message(chat_id=self._telegram_user_id, text=message)
              

def secure_get(url):
    try:
        response = requests.get(url)
    except Exception as e:
        print(f"Exception occured during call : {e}")
        return None
    return response


def signal_handler(signal, frame):
    print("Caught a Ctrl C signal, quitting ..")
    sys.exit(0)


def hashing(query_string, api_secret):
    return hmac.new(
        api_secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def get_timestamp():
    return int(time.time() * 1000)

def init_logger(logger_name: str='UnNamedProcess'):
    LOG_LEVEL = logging.INFO
    LOGFORMAT = "%(log_color)s%(asctime)s%(reset)s | %(log_color)s%(name)s%(reset)s | %(log_color)s%(levelname)s%(reset)s | %(message)s"
    logging.root.setLevel(LOG_LEVEL)
    formatter = ColoredFormatter(LOGFORMAT)
    stream = logging.StreamHandler()
    stream.setLevel(LOG_LEVEL)
    stream.setFormatter(formatter)
    log = logging.getLogger(logger_name)
    log.setLevel(LOG_LEVEL)
    log.addHandler(stream)
    return log


def compute_signature(payload, key):
    return hashing(urlencode(dict(sorted(payload.items()))), key)
    
def get_root_path():
    utils_folder = os.path.dirname(os.path.abspath(__file__))
    root_folder = os.path.dirname(utils_folder)
    return root_folder

def get_data_path():
    root_folder = get_root_path()
    data_folder = os.path.join(root_folder, "data/")
    return data_folder
