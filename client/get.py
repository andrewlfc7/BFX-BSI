
import aiohttp
import ssl
from typing import List, Optional
from dataclasses import dataclass, field

@dataclass
class PUBLICGetLinks:
    MARKETS: str = "https://api.bfx.trade/markets"
    TRADES_HISTORY: str = "https://api.bfx.trade/markets/trades"
    L2BOOK: str = "https://api.bfx.trade/markets/orderbook"
    FUNDING_RATE: str = "https://api.bfx.trade/markets/fundingrate"
    CANDLES: str = "https://api.bfx.trade/candles"


@dataclass
class EnvironmentLinks:
    base_url: str

    @property
    def ACCOUNT(self) -> str:
        return f"{self.base_url}/account"

    @property
    def ORDERS(self) -> str:
        return f"{self.base_url}/orders"

    @property
    def FILLS(self) -> str:
        return f"{self.base_url}/fills"

    @property
    def POSITIONS(self) -> str:
        return f"{self.base_url}/positions"

    @property
    def PROFILE(self) -> str:
        return f"{self.base_url}/profile"
    @property
    def CANCEL_ALL(self) -> str:
        return f"{self.base_url}/orders/cancel_all"




@dataclass
class PrivateLinks:
    mainnet: EnvironmentLinks = field(default_factory=lambda: EnvironmentLinks("https://api.bfx.trade"))
    testnet: EnvironmentLinks = field(default_factory=lambda: EnvironmentLinks("https://api.testnet.bfx.trade"))




class PublicClient:

    def __init__(self, symbol: str) -> None:
        self.symbol = symbol

        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self.session = aiohttp.ClientSession(connector=connector)

    async def __aenter__(self):
        return self

    async def _fetch_data(self, url: str, params: dict = None) -> List:
        headers = {"accept": "application/json"}

        async with self.session.get(url, params=params, headers=headers) as response:
            try:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Error: {response.status}")
                    return []
            except aiohttp.ClientError as e:
                print(f"Exception: {e}")

    async def klines(self, period: int, timestamp_from: int, timestamp_to: int) -> List:
        params = {
            "market_id":  self.symbol,
            "timestamp_from": timestamp_from,
            "timestamp_to": timestamp_to,
            "period": period
        }
        return await self._fetch_data(PUBLICGetLinks.CANDLES, params)

    async def trades(self, p_limit: int = 50, p_page: int = 0, p_order: str = "DESC") -> List:
        params = {
            "market_id":  self.symbol,
            "p_limit": p_limit,
            "p_page": p_page,
            "p_order": p_order
        }
        return await self._fetch_data(PUBLICGetLinks.TRADES_HISTORY, params)

    async def orderbook(self, p_limit: int = 1, p_page: int = 0, p_order: str = "DESC") -> List:
        params = {
            "market_id":  self.symbol,
            "p_limit": p_limit,
            "p_page": p_page,
            "p_order": p_order
        }
        return await self._fetch_data(PUBLICGetLinks.L2BOOK, params)

    async def funding_rate(self, p_limit: int = 100) -> List:
        params = {
            "market_id":  self.symbol,
            "p_limit": p_limit
        }
        return await self._fetch_data(PUBLICGetLinks.FUNDING_RATE, params)

    async def markets(self) -> List:
        params = {"market_id":  self.symbol}
        return await self._fetch_data(PUBLICGetLinks.MARKETS, params)

    async def __aexit__(self, *args, **kwargs) -> None:
        await self.session.close()



