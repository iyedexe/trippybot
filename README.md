# TriangularArbitragePyBot

use : 
client webstream implementation:
https://github.com/binance/binance-signature-examples/blob/master/python/websocket-api/websocket_api_client.py

ws content:
https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md


good inspiration:
https://dev.to/ken_mwaura1/crypto-data-bot-using-python-binance-websockets-and-postgresql-db-5fnd

potential improvement:
https://www.thealgorists.com/Algo/ShortestPaths/Arbitrage

How to setup :
>python -m venv dodrio
windows : >venv\dodrio\Scripts\activate.bat
linux :
>source venv/dodrio/bin/activate
>pip install -r requirements.txt


# sell to the bid
# buy from the ask

# bid X, ask Y

# BNB -> BTC -> ETH -> BNB            

# SELL BNB/BTC
# cost : 1 BNB * (100 - Fee1%)/100
# get : Y1 BTC

# BUY ETH/BTC
# cost : 1 BTC * Fee2%
# get : 1/X2 ETH

# SELL ETH/BNB
# cost : 1 ETH * Fee3%
# get : Y3 BNB

# FinalBNB = StartingBNB * (100 - Fee1%) * Y1 * (100 - Fee2%) * 1/X2 * (100 - Fee3%) * Y3


#Important : 
Timing security

    SIGNED requests also require a timestamp parameter which should be the current millisecond timestamp.
    An additional optional parameter, recvWindow, specifies for how long the request stays valid.
        If recvWindow is not sent, it defaults to 5000 milliseconds.
        Maximum recvWindow is 60000 milliseconds.
    Request processing logic is as follows:

  if (timestamp < (serverTime + 1000) && (serverTime - timestamp) <= recvWindow) {
    // process request
  } else {
    // reject request
  }

Serious trading is about timing. Networks can be unstable and unreliable, which can lead to requests taking varying amounts of time to reach the servers. With recvWindow, you can specify that the request must be processed within a certain number of milliseconds or be rejected by the server.

It is recommended to use a small recvWindow of 5000 or less!

#
Base Currency
The base currency is the first currency listed in a currency pair. It is the currency that is being bought or sold. For example, in the EUR/USD currency pair, the euro (EUR) is the base currency.

Quote Currency
The quote currency is the second currency listed in a currency pair. It is used to determine the value of the 