# BFX-BSI
## Orderflow trading bot based on BSI for BFX using Binance, Bybit, Hyperliquid trades data


## algo/trading_algo.py

Contains a class responsible for trading operations, including starting the WebSocket feeds for the various exchanges and subscribing to the trades feeds, as well as fetching market data and account information from BFX such as positions and fills within the last 4 minutes. As well processing the data from the feeds to generate the signals based on the orderflow

## bsi/bsi.py

Contains a class dedicated to calculating the Buy/Sell Imbalance (BSI) for given coin trade data. The class initializes by setting up core parameters, including the coin base and a warmup period, and manages a buffer for incoming trade data. Once enough data is gathered during the warmup period, the class processes it to calculate the BSI, which is then used to generate trading signals. More information and the formula behind BSI can be found in the articles listed at the end.

## ws_feeds/ws.py

Contains a class that manages WebSocket connections to multiple exchanges for a specified coin, given its based e.g BTC. It subscribes to real-time trade feeds from various exchanges. The class efficiently handles and parses incoming trade data and passes it to a Buy/Sell Imbalance (BSI) calculator for generating trading signals.


## client/get.py

Contains a class for accessing public market data from a specified cryptocurrency symbol. This class uses asynchronous HTTP requests to fetch various types of market information, such as trade history, order book data, funding rates, and kline data


## BFX-BSI/main.py
If you want to try it, then you need an API and Secret key from Blast Futures Exchange (BFX). The bot is currently set for BTC, but it can be easily changed to different coins. However, you would need to change the WS class as well as in the main script. Also play around with the decay(kappa)

### To - Do

Find the best kappa based on the holding period of interest.
Add more exchanges, and also include spot trading, since the bot is currently only using perps trades.



## DISCLAIMER: Nothing in this repository constitutes financial advice (and therefore, please use at your own risk). It is tailored primarily for learning purposes, and is highly unlikely you will make profits trading this strategy. I will not accept liability for any loss or damage including, without limitation to, any loss of profit which may arise directly or indirectly from use of or reliance on this software.


## Inspired by the following articles : https://markrbest.github.io/bitcoin-elasticity-and-market-crashes/
https://tr8dr.github.io/BuySellImbalance/

