import requests
import logging
import hmac
import hashlib
import time
from urllib.parse import urlencode
from colorlog import ColoredFormatter
import sys

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
    LOG_LEVEL = logging.DEBUG
    LOGFORMAT = "%(log_color)s%(asctime)s%(reset)s | %(log_color)s%(name)s%(reset)s | %(log_color)s%(levelname)s%(reset)s | %(message)s"
    logging.root.setLevel(LOG_LEVEL)
    formatter = ColoredFormatter(LOGFORMAT)
    stream = logging.StreamHandler()
    stream.setLevel(LOG_LEVEL)
    stream.setFormatter(formatter)
    log = logging.getLogger('OrderHandler')
    log.setLevel(LOG_LEVEL)
    log.addHandler(stream)
    return log


def compute_signature(payload, key):
    return hashing(urlencode(dict(sorted(payload.items()))), key)
    
