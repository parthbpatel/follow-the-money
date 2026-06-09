import requests


class MarketDataFetcher:

    @staticmethod
    def get_crypto_prices():

        url = (
            "https://api.coingecko.com/api/v3/simple/price"
            "?ids=bitcoin,ethereum"
            "&vs_currencies=usd"
        )

        response = requests.get(url)

        return response.json()
