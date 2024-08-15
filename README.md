# Trippy Bot :
## Presentation :
* This is a start of a framework/codebase for creating strategies and backtesting them.
* The reason for this rogue framework (and not using backtrader, vectorbt or even quantconnect)
    - Working with asynchronous market data signals 
    - Flexibility with market data fields and frequency
    - Simplicity and ease of mind of being batman.

## Strategies :
### Triangular arbitrage:
* Jumps over 3 crypto coins by means of selling and buying associated pairs, so that a positive PNL is realised just with 3 transactions.  
#### Strategy profitability evaluation:
Follow the simple example of the cycle based on BNB, BTC and ETH in that order :  

BNB -> BTC -> ETH -> BNB              
a possible path is :  
SELL BNB/BTC  
    - unitary cost : 1 BNB  
    - get : Y1 * (1 - Fee1%/100) BTC  
BUY ETH/BTC  
    - unitairy cost : 1 BTC   
    - get : 1/X2 *(1 - Fee2%/100) ETH  
SELL ETH/BNB  
    - unitairy cost : 1 ETH   
    - get : Y3 *(1 - Fee3%/100) BNB  

==> FinalBNB = StartingBNB * (100 - Fee1%) * Y1 * (100 - Fee2%) * 1/X2 * (100 - Fee3%) * Y3  
r is the profitabilty of a cycle :  
**r = (1 - Fee1%/100) * (1 - Fee2%/100) * (1 - Fee3%/100) * Y1 * Y3 * 1/X2 **    
**Startegy is profitable is made if r>1**       

### Reinforcement learning:

### Supertrend:

# Implementation choices :

## Order size:
when we say we BUY(<-) a PAIR USD/EUR we are buying the base, ie USD and selling the quote, ie EUR.  
==> we are spending EUR.  
when we say we SELL(->) a PAIR USD/EUR we are selling the base, ie USD and buying the quote, ie EUR.  
==> we are spending USD  

this resulted in the choice where   
    - **buy orders are sized in quote currency**  
    - **sell orders are sized in base currency**  


# Infra
After some research and experimentation, latency can be critical in such strategy and any way to minimize it is welcome.   
as per this awesome work : https://docs.google.com/spreadsheets/d/1W345Qgp1QdcKdyg_hRkzl79OTkGVtxMJJZnJGjtdSp4/edit#gid=0  

| US East N. Virginia (us-east-1)  | US West N. California (us-west-1)  | Frankfurt (eu-central-1)  | London (eu-west-1)  |  Hong Kong (ap-east-1) | Seoul (ap-northeast-2) | Singapore (ap-southeast-1)  | Tokyo (ap-northeast-1)|
|----------------------------------|------------------------------------|---------------------------|---------------------|------------------------|------------------------|-----------------------------|-----------------------|
|				0.424			   |                    0.16	        |         0.268	            |       0.269         |         0.075          |         0.072          |           0.206             |        0.023          |

Each value is the round trip latency in seconds for a REST fetch_ticker() call via the Python ccxt library (average of 10 serial iterations) from the specified server location. 			
the lowest latency is if the app is hosted on aws Tokyo. (ap-northeast-1)
# References :

## APIs used :   
OIHTTP for async WS :      
    https://docs.aiohttp.org/en/stable/client_reference.html       
ASYNCIO for general async:   
    https://docs.python.org/3/library/asyncio-sync.html#asyncio.Event        
BINANCE WebSockets API:      
    https://binance-docs.github.io/apidocs/websocket_api/en/#signed-request-example-rsa      
BINANCE Streams Websockets API:   
    https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md       

## Inspiration:        
### client webstream implementation:    
https://github.com/binance/binance-signature-examples/blob/master/python/websocket-api/websocket_api_client.py    
### good inspiration:
https://dev.to/ken_mwaura1/crypto-data-bot-using-python-binance-websockets-and-postgresql-db-5fnd    
### potential improvement:
https://www.thealgorists.com/Algo/ShortestPaths/Arbitrage    
### Market data ressource :
https://polygon.io/flat-files/crypto-trades    
https://www.cryptoarchive.com.au/downloads     

# How to setup :
    >python -m venv venv       
    windows :  
    >venv\Scripts\activate.bat  
    linux :    
    >source venv/bin/activate   
    >pip install -r requirements.txt   


# TODO :
* Strategy runner:
    - Strategy evaluate if quantity on book is enough.
    - Handle and process exec quantity
    - After processing signal, use only last update

* DevOps:
    - Automatic Jenkins deployment on aws zone    
    - Grafana monitoring     
        - Technical metrics on process health, network traffic, server cpu and mem    
        - Functional metrics on current balance, list of trades, PNL per trade and global    

* Strategies :
    - Create book recorder
    - Create strategy backtester
    - ML reinforcement learning
    - Arbitrage strategy using bellmanford
