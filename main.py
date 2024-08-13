import logging
import asyncio
from algo.trading_algo import TradingAlgorithm

async def main():
    logging.basicConfig(level=logging.INFO)
    trading_algorithm = TradingAlgorithm(
        coin_base="BTC",
        warmup_period=100,
        api_key="",
        secret_key="",
        base_url="https://api.bfx.trade"
    )
    await trading_algorithm.run()
if __name__ == "__main__":
    asyncio.run(main())








