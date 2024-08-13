# BFX-BSI
Orderflow trading bot based on BSI for BFX using Binance, Bybit, Hyperliquid trades data


algo/trading_algo.py

Contains a class responsible for trading operations, including starting the WebSocket feeds for the various exchanges and subscribing to the trades feeds, as well as fetching market data and account information from BFX such as positions and fills within the last 4 minutes. As well processing the data from the feeds to generate the signals based on the orderflow


DISCLAIMER: Nothing in this repository constitutes financial advice (and therefore, please use at your own risk). It is tailored primarily for learning purposes, and is highly unlikely you will make profits trading this strategy. I will not accept liability for any loss or damage including, without limitation to, any loss of profit which may arise directly or indirectly from use of or reliance on this software.


Inspired by the following articles : https://markrbest.github.io/bitcoin-elasticity-and-market-crashes/
https://tr8dr.github.io/BuySellImbalance/