# TriangularArbitragePyBot

use : 
client webstream implementation:
https://github.com/binance/binance-signature-examples/blob/master/python/websocket-api/websocket_api_client.py

ws content:
https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md


good inspiration:
https://dev.to/ken_mwaura1/crypto-data-bot-using-python-binance-websockets-and-postgresql-db-5fnd


How to setup :
python -m venv dodrio


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
