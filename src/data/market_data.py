import requests

from src.logger import log
from src.utils.performance import PerformanceTimer


class MarketDataFetcher:

    @staticmethod
    def get_crypto_prices():

        url = (
            "https://api.coingecko.com/api/v3/simple/price"
            "?ids=bitcoin,ethereum"
            "&vs_currencies=usd"
        )

        log.info("Requesting crypto prices from %s", url)
        with PerformanceTimer("CoinGecko", record_key="CoinGecko"):
            response = requests.get(url)
            response.raise_for_status()
        data = response.json()
        log.info("Received crypto prices: %s", data)

        return data
