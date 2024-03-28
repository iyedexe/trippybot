# Implementation choices :

## Order size:
when we say we BUY(<-) a PAIR USD/EUR we are buying the base, ie USD and selling the quote, ie EUR.  
==> we are spending EUR.  
when we say we SELL(->) a PAIR USD/EUR we are selling the base, ie USD and buying the quote, ie EUR.  
==> we are spending USD  

this resulted in the choice where   
    - **buy orders are sized in quote currency**  
    - **sell orders are sized in base currency**  

## Strategy profitability evaluation:
Follow the simple example of the cycle based on BNB, BTC and ETH in that order :  

BNB -> BTC -> ETH -> BNB              
a possible path is :  
SELL BNB/BTC  
    - unitary cost : 1 BNB * (100 - Fee1%)/100  
    - get : Y1 BTC  
BUY ETH/BTC  
    - unitairy cost : 1 BTC * Fee2%  
    - get : 1/X2 ETH  
SELL ETH/BNB  
    - unitairy cost : 1 ETH * Fee3%  
    - get : Y3 BNB  

==> FinalBNB = StartingBNB * (100 - Fee1%) * Y1 * (100 - Fee2%) * 1/X2 * (100 - Fee3%) * Y3  
r is the profitabilty of a cycle :  
**r = (100 - Fee1%) * Y1 * (100 - Fee2%) * 1/X2 * (100 - Fee3%) * Y3**    
**Startegy is profitable is made if r>1**       

# Infra
After some research and experimentation, latency can be critical in such strategy and any way to minimize it is welcome.   
as per this awesome work : https://docs.google.com/spreadsheets/d/1W345Qgp1QdcKdyg_hRkzl79OTkGVtxMJJZnJGjtdSp4/edit#gid=0  

| US East N. Virginia (us-east-1)  | US West N. California (us-west-1)  | Frankfurt (eu-central-1)  | London (eu-west-1)  |  Hong Kong (ap-east-1) | Seoul (ap-northeast-2) | Singapore (ap-southeast-1)  | Tokyo (ap-northeast-1)|
|----------------------------------|------------------------------------|---------------------------|---------------------|------------------------|------------------------|-----------------------------|-----------------------|
|				0.424			   |                    0.16	        |         0.268	            |       0.269         |         0.075          |         0.072          |           0.206             |        0.023          |

Each value is the round trip latency in seconds for a REST fetch_ticker() call via the Python ccxt library (average of 10 serial iterations) from the specified server location. 			
the lowest latency is if the app is hosted on aws Tokyo. (ap-northeast-1)
# References :
use : 
## client webstream implementation:
https://github.com/binance/binance-signature-examples/blob/master/python/websocket-api/websocket_api_client.py

## ws content:
https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md

## good inspiration:
https://dev.to/ken_mwaura1/crypto-data-bot-using-python-binance-websockets-and-postgresql-db-5fnd

## potential improvement:
https://www.thealgorists.com/Algo/ShortestPaths/Arbitrage

## APIs used :
OIHTTP for async WS :   
    https://docs.aiohttp.org/en/stable/client_reference.html    
ASYNCIO for general async:
    https://docs.python.org/3/library/asyncio-sync.html#asyncio.Event     
BINANCE WebSockets API:   
    https://binance-docs.github.io/apidocs/websocket_api/en/#signed-request-example-rsa   
BINANCE Streams Websockets API:
    https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md    

# How to setup :
    >python -m venv venv       
    windows :  
    >venv\Scripts\activate.bat  
    linux :    
    >source venv/bin/activate   
    >pip install -r requirements.txt   

# General doc
## Binance server time sync : 
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

## Binance LOT SIZE
LOT_SIZE

    ExchangeInfo format:

  {
    "filterType": "LOT_SIZE",
    "minQty": "0.00100000",
    "maxQty": "100000.00000000",
    "stepSize": "0.00100000"
  }

The LOT_SIZE filter defines the quantity (aka "lots" in auction terms) rules for a symbol. There are 3 parts:

    minQty defines the minimum quantity/icebergQty allowed.
    maxQty defines the maximum quantity/icebergQty allowed.
    stepSize defines the intervals that a quantity/icebergQty can be increased/decreased by.

In order to pass the lot size, the following must be true for quantity/icebergQty:

    quantity >= minQty
    quantity <= maxQty
    quantity % stepSize == 0

# FX Pairs
Base Currency
The base currency is the first currency listed in a currency pair. It is the currency that is being bought or sold. For example, in the EUR/USD currency pair, the euro (EUR) is the base currency.

Quote Currency
The quote currency is the second currency listed in a currency pair. It is used to determine the value of the 
