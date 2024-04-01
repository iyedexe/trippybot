# TODO :
* Include fees
* Handle and process exec quantity
* Make critical the signal process function, and when back to data processing, aggregate updates
* FeedHandler in AIOHTTP async
* App deployment in AWS Tokyo region, automatic restart daily, file logging    
* App monitoring via graphana:    
    - technical metrics on process health, network traffic, server cpu and mem    
    - functional metrics on current balance, list of trades, PNL per trade and global    
* Add strategy backtesting method into framework
* Make code generic and working for different exchnage brokers
* Use framework for different strategies
    - Basic Cross exchange arbitrage (could be beneficial)
    - BellmanFord path finder arbitrage (for the maths)
    - Triangular cross exchange arbitrage (very promising)
 

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

# How to setup :
    >python -m venv venv       
    windows :  
    >venv\Scripts\activate.bat  
    linux :    
    >source venv/bin/activate   
    >pip install -r requirements.txt   
