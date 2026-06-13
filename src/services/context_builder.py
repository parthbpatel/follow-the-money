from typing import Any

from src.data.market_data import MarketDataFetcher
from src.data.tavily_search import TavilySearchService
from src.logger import log
from src.utils.performance import PerformanceTimer


class ContextBuilder:
    """Builds a grounded context payload with market data, Tavily news and source references."""

    def __init__(self, search_service: TavilySearchService | None = None) -> None:
        self.search_service = search_service or TavilySearchService()

    def build(self, queries: list[str] | None = None) -> dict[str, Any]:
        queries = queries or [
            "global capital flows today",
            "Federal Reserve latest policy",
            "RBI latest announcement",
            "India economy latest developments",
            "AI infrastructure investments",
            "semiconductor investments",
            "sovereign wealth fund investments",
            "infrastructure spending projects",
        ]

        market_data = MarketDataFetcher.get_crypto_prices()
        news_items: list[dict[str, Any]] = []
        sources: list[str] = ["CoinGecko simple price API"]

        for query in queries:
            timer = PerformanceTimer(f"Tavily query='{query}'", record_key="Tavily Total")
            with timer:
                results = self.search_service.search(query=query, max_results=3)
            log.info("[PERF] Tavily query='%s' took %.2f sec", query, timer.duration)
            for result in results:
                news_items.append({"query": query, **result})
                sources.append(result.get("url") or f"Tavily search: {query}")

        context_text = self._render_context(market_data, news_items)
        log.info("ContextBuilder completed with %d market data entries and %d news items", len(market_data), len(news_items))

        return {
            "context": context_text,
            "sources": list(dict.fromkeys(sources)),
            "market_data": market_data,
            "news_items": news_items,
        }

    @staticmethod
    def _render_context(market_data: dict[str, Any], news_items: list[dict[str, Any]]) -> str:
        market_lines = [f"- {symbol}: {values}" for symbol, values in market_data.items()]
        news_lines = []

        for item in news_items:
            title = item.get("title", "Untitled")
            url = item.get("url", "")
            content = item.get("content", "")
            query = item.get("query", "")
            news_lines.append(f"- Query: {query}\n  Title: {title}\n  URL: {url}\n  Summary: {content}")

        return "\n".join(
            [
                "MARKET DATA:\n" + "\n".join(market_lines),
                "\nNEWS:\n" + ("\n\n".join(news_lines) if news_lines else "Data unavailable."),
                "\nSOURCES:\n" + "\n".join([f"- {source}" for source in dict.fromkeys(["CoinGecko", *[item.get('url', 'Tavily search') for item in news_items]])]),
            ]
        )
