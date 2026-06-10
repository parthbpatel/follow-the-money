import requests

from src.logger import log


class MarketDataFetcher:

    @staticmethod
    def get_crypto_prices():

        url = (
            "https://api.coingecko.com/api/v3/simple/price"
            "?ids=bitcoin,ethereum"
            "&vs_currencies=usd"
        )

        log.info("Requesting crypto prices from %s", url)
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        log.info("Received crypto prices: %s", data)

        return data
