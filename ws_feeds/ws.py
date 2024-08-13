import asyncio
import websockets
import json
import logging
import aiohttp
import ssl
from datetime import datetime
from bsi.bsi import BSICalculator



class MultiExchangeWebSocket:
    def __init__(self, coin_base="BTC", warmup_period=100):
        self.coin_base = coin_base
        self.connections = {}
        self.exchange_info = self.setup_exchange_info()
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        self.bsi_calculator = BSICalculator(coin_base, warmup_period)

    def setup_exchange_info(self):
        """
        Set up the WebSocket URLs and subscription messages for each exchange.
        """
        return {
            "Binance": {
                "url": f"wss://fstream.binance.com/ws/{self.coin_base.lower()}usdt@aggTrade",
                "subscription": None
            },
            "Bybit": {
                "url": "wss://stream.bybit.com/v5/public/linear",
                "subscription": {
                    "op": "subscribe",
                    "args": [f"publicTrade.{self.coin_base}USDT"]
                }
            },
            "Hyperliquid": {
                "url": "wss://api.hyperliquid.xyz/ws",
                "subscription": {
                    "method": "subscribe",
                    "subscription": {
                        "type": "trades",
                        "coin": self.coin_base
                    }
                }
            }
        }

    async def connect(self, exchange, url, subscription_message):
        """
        Connects to the WebSocket feed for a specific exchange and subscribes to the trade feed.
        """
        try:
            async with websockets.connect(url, ssl=self.ssl_context) as websocket:
                self.connections[exchange] = websocket
                if subscription_message:
                    await websocket.send(json.dumps(subscription_message))
                logging.info(f"Connected and subscribed to {exchange}")
                await self.receive_messages(exchange, websocket)
        except websockets.InvalidStatusCode as e:
            logging.error(f"Error connecting to {exchange}: {e}")
        except Exception as e:
            logging.error(f"Error connecting to {exchange}: {e}")

    async def receive_messages(self, exchange, websocket):
        """
        Receives messages from the WebSocket feed and handles them.
        """
        try:
            async for message in websocket:
                data = json.loads(message)
                await self.handle_message(exchange, data)
        except websockets.ConnectionClosed as e:
            logging.warning(f"Connection closed for {exchange}: {e}")
        except Exception as e:
            logging.error(f"Error receiving message from {exchange}: {e}")

    async def handle_message(self, exchange, data):
        """
        Centralized handling of incoming messages from different exchanges.
        """
        try:
            if exchange == "Binance":
                await self.handle_binance(data)
            elif exchange == "Bybit":
                await self.handle_bybit(data)
            elif exchange == "Hyperliquid":
                await self.handle_hyperliquid(data)
        except KeyError as e:
            logging.error(f"Error handling message from {exchange}: {e}")

    async def handle_binance(self, data):
        """
        Handle Binance data and extract common fields.
        """
        processed_data = {
            "symbol": f"{self.coin_base}USDT",
            "price": float(data['p']),
            "quantity": float(data['q']),
            "side": "buy" if data['m'] is False else "sell",
            "timestamp": datetime.fromtimestamp(data['T'] / 1000)
        }
        await self.bsi_calculator.process_data("Binance", processed_data)

    async def handle_bybit(self, data):
        """
        Handle Bybit data and extract common fields.
        """
        trades = data.get('data', [])
        for trade in trades:
            processed_data = {
                "symbol": trade['s'],
                "price": float(trade['p']),
                "quantity": float(trade['v']),
                "side": trade['S'].lower(),
                "timestamp": datetime.fromtimestamp(trade['T'] / 1000)
            }
            await self.bsi_calculator.process_data("Bybit", processed_data)

    async def handle_hyperliquid(self, data):
        """
        Handle Hyperliquid data and extract common fields.
        """
        if data.get('channel') == 'trades':
            trades = data['data']
            for trade in trades:
                processed_data = {
                    "symbol": trade['coin'],
                    "price": float(trade['px']),
                    "quantity": float(trade['sz']),
                    "side": 'buy' if trade['side'] == 'B' else 'sell',
                    "timestamp": datetime.fromtimestamp(trade['time'] / 1000)
                }
                await self.bsi_calculator.process_data("Hyperliquid", processed_data)
        else:
            logging.info(f"Received non-trade data from Hyperliquid: {data}")

    async def subscribe(self):
        """
        Initiates the connection and subscription for all exchanges.
        """
        tasks = []
        for exchange, info in self.exchange_info.items():
            tasks.append(self.connect(exchange, info["url"], info["subscription"]))
        await asyncio.gather(*tasks)

    async def run(self):
        """
        Runs the WebSocket connections and handles subscriptions.
        """
        await self.subscribe()

